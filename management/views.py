from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.http import JsonResponse
import json

from .models import Teacher, Student, Class, Enrollment, Attendance
from .forms import ClassForm

# --- Helper Functions for Role Checks ---

def is_teacher(user):
    return hasattr(user, 'teacher')

def is_student(user):
    return hasattr(user, 'student')

def is_admin(user):
    return user.is_staff

# --- Main Dashboard View ---

class DashboardView(LoginRequiredMixin, View):
    """
    Redirects user to the correct dashboard based on their role.
    """
    def get(self, request, *args, **kwargs):
        if is_teacher(request.user):
            return redirect('teacher_dashboard')
        elif is_student(request.user):
            return redirect('student_dashboard')
        elif is_admin(request.user):
            return redirect('admin/')
        else:
            # Handle users who are logged in but not linked
            # to a Teacher or Student profile (e.g., superusers).
            messages.info(request, "Your account is not linked to a Teacher or Student profile.")
            return redirect('login') # Or a different page

# --- Teacher Views ---

class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Dashboard for Teachers.
    """
    def test_func(self):
        return is_teacher(self.request.user)

    def get(self, request, *args, **kwargs):
        teacher = request.user.teacher
        now = timezone.now().time()
        
        # Get all classes for this teacher
        teacher_classes = Class.objects.filter(teacher=teacher)

        # Calculate total unique students across all classes taught by this teacher
        total_students = Student.objects.filter(enrollments__class_obj__teacher=teacher).distinct().count()

        # Dashboard stats
        current_classes = teacher_classes.filter(start_time__lte=now, end_time__gte=now)
        upcoming_classes = teacher_classes.filter(start_time__gt=now).order_by('start_time')
        
        context = {
            'total_classes': teacher_classes.count(),
            'total_students': total_students,
            'current_classes': current_classes,
            'upcoming_classes': upcoming_classes,
            'all_classes': teacher_classes.order_by('start_time'),
        }
        return render(request, 'teacher_dashboard.html', context)

class ClassCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Teacher: Create a new class.
    """
    def test_func(self):
        return is_teacher(self.request.user)

    def get(self, request, *args, **kwargs):
        form = ClassForm()
        return render(request, 'class_form.html', {'form': form, 'title': 'Create Class'})

    def post(self, request, *args, **kwargs):
        form = ClassForm(request.POST, teacher=request.user.teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Class created successfully.")
            return redirect('teacher_dashboard')
        return render(request, 'class_form.html', {'form': form, 'title': 'Create Class'})

class ClassUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Teacher: Update an existing class.
    """
    def test_func(self):
        return is_teacher(self.request.user)

    def get(self, request, pk, *args, **kwargs):
        class_obj = get_object_or_404(Class, pk=pk, teacher=request.user.teacher)
        form = ClassForm(instance=class_obj)
        return render(request, 'class_form.html', {'form': form, 'title': 'Update Class'})

    def post(self, request, pk, *args, **kwargs):
        class_obj = get_object_or_404(Class, pk=pk, teacher=request.user.teacher)
        form = ClassForm(request.POST, instance=class_obj, teacher=request.user.teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Class updated successfully.")
            return redirect('teacher_dashboard')
        return render(request, 'class_form.html', {'form': form, 'title': 'Update Class'})


class ManageEnrollmentsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Teacher: Add or remove students from a class.
    """
    template_name = 'manage_enrollments.html'

    def test_func(self):
        return is_teacher(self.request.user)
    
    def setup(self, request, *args, **kwargs):
        """Get the class object and verify teacher ownership."""
        super().setup(request, *args, **kwargs)
        class_id = self.kwargs.get('class_id')
        self.class_obj = get_object_or_404(Class, id=class_id, teacher=request.user.teacher)

    def get_context_data(self):
        """Get enrolled and unenrolled students."""
        # Get IDs of students already enrolled
        enrolled_student_ids = self.class_obj.enrollments.values_list('student_id', flat=True)
        
        # Get student objects
        enrolled_students = Student.objects.filter(id__in=enrolled_student_ids)
        unenrolled_students = Student.objects.exclude(id__in=enrolled_student_ids)
        
        return {
            'class_obj': self.class_obj,
            'enrolled_students': enrolled_students,
            'unenrolled_students': unenrolled_students,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        if 'enroll_student' in request.POST:
            student_id = request.POST.get('enroll_student')
            try:
                student = Student.objects.get(id=student_id)
                # Use get_or_create to avoid duplicate enrollments
                Enrollment.objects.get_or_create(student=student, class_obj=self.class_obj)
                messages.success(request, f"{student.user.get_full_name() or student.user.username} has been enrolled.")
            except Student.DoesNotExist:
                messages.error(request, "Student not found.")
        
        elif 'unenroll_student' in request.POST:
            student_id = request.POST.get('unenroll_student')
            try:
                student = Student.objects.get(id=student_id)
                # Find and delete the enrollment
                Enrollment.objects.filter(student=student, class_obj=self.class_obj).delete()
                messages.success(request, f"{student.user.get_full_name() or student.user.username} has been unenrolled.")
            except Student.DoesNotExist:
                messages.error(request, "Student not found.")
        
        # Redirect back to the same page to show updated lists
        return redirect('manage_enrollments', class_id=self.class_obj.id)


class MarkAttendanceView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Teacher: Mark attendance for a class manually.
    """
    def test_func(self):
        return is_teacher(self.request.user)
    
    def setup(self, request, *args, **kwargs):
        """
        Store class object and check ownership.
        """
        super().setup(request, *args, **kwargs)
        class_id = self.kwargs.get('class_id')
        self.class_obj = get_object_or_404(Class, id=class_id, teacher=request.user.teacher)
        self.today = timezone.now().date()

    def get(self, request, *args, **kwargs):
        # Check if attendance is within the allowed time
        now = timezone.now().time()
        is_active = self.class_obj.is_active_now
        
        if not is_active:
             messages.warning(request, f"Attendance can only be marked between {self.class_obj.start_time.strftime('%I:%M %p')} and {self.class_obj.end_time.strftime('%I:%M %p')}.")

        # Get enrolled students
        enrolled_students = Student.objects.filter(enrollments__class_obj=self.class_obj)
        
        # Get existing attendance records for today
        existing_attendance = Attendance.objects.filter(
            class_obj=self.class_obj, 
            date=self.today
        ).values_list('student_id', 'status')
        
        # Create a dict for easy lookup in the template
        attendance_dict = dict(existing_attendance)
        
        student_list = []
        for student in enrolled_students:
            student_list.append({
                'id': student.id,
                'name': student.user.get_full_name() or student.user.username,
                'status': attendance_dict.get(student.id, 'A') # Default to Absent
            })

        context = {
            'class_obj': self.class_obj,
            'students': student_list,
            'is_active': is_active, # Pass flag to template
            'today': self.today,
        }
        return render(request, 'mark_attendance.html', context)

    def post(self, request, *args, **kwargs):
        # **CRITICAL**: Re-check time on POST to prevent exploits
        now = timezone.now()
        if not self.class_obj.is_active_now:
            messages.error(request, "Attendance submission failed. The time window has closed.")
            return redirect('mark_attendance', class_id=self.class_obj.id)
        
        # Get all student IDs from the form
        student_ids = request.POST.getlist('student_id')
        
        for student_id in student_ids:
            try:
                student = Student.objects.get(id=student_id)
                # Check if this student is actually enrolled
                if not Enrollment.objects.filter(student=student, class_obj=self.class_obj).exists():
                    continue # Skip if not enrolled

                status = request.POST.get(f'status_{student_id}')
                if status not in ['P', 'A', 'L']:
                    continue # Invalid status

                # Use update_or_create to handle existing records
                Attendance.objects.update_or_create(
                    student=student,
                    class_obj=self.class_obj,
                    date=self.today,
                    defaults={'status': status, 'timestamp': now}
                )
            except Student.DoesNotExist:
                continue # Skip if student ID is invalid

        messages.success(request, "Attendance submitted successfully.")
        return redirect('teacher_dashboard')

class TeacherAttendanceHistoryView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Teacher: View all attendance records for a specific class.
    """
    def test_func(self):
        return is_teacher(self.request.user)
    
    def get(self, request, class_id, *args, **kwargs):
        class_obj = get_object_or_404(Class, id=class_id, teacher=request.user.teacher)
        
        # Optional: Filter by date
        date_str = request.GET.get('date')
        
        # Optimize query with select_related to fetch student and user details in one go
        queryset = Attendance.objects.filter(class_obj=class_obj).select_related('student', 'student__user')
        
        if date_str:
            queryset = queryset.filter(date=date_str)
            
        # Order by date descending, then by student's last name
        history = queryset.order_by('-date', 'student__user__last_name')
        
        # Get a list of unique dates for the filter dropdown
        dates = Attendance.objects.filter(class_obj=class_obj).dates('date', 'day', order='DESC')
        
        context = {
            'class_obj': class_obj,
            'history': history,
            'dates': dates,
            'selected_date': date_str,
        }
        return render(request, 'teacher_attendance_history.html', context)


# --- NEW SCANNER VIEWS ---

class ScannerAttendanceView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Teacher: Renders the barcode scanner page.
    """
    def test_func(self):
        return is_teacher(self.request.user)

    def get(self, request, class_id, *args, **kwargs):
        class_obj = get_object_or_404(Class, id=class_id, teacher=request.user.teacher)
        context = {
            'class_obj': class_obj,
            'is_active': class_obj.is_active_now, # Check if class is active
        }
        return render(request, 'scan_attendance.html', context)


class MarkAttendanceAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    API-like view to mark attendance from a barcode scan.
    This view is called by JavaScript, not a regular form.
    """
    def test_func(self):
        return is_teacher(self.request.user)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            student_id_str = data.get('student_id')
            class_id = data.get('class_id')
            
            # 1. Get Class and check teacher ownership
            class_obj = get_object_or_404(Class, id=class_id, teacher=request.user.teacher)
            
            # 2. **CRITICAL: Enforce Time Constraint**
            if not class_obj.is_active_now:
                return JsonResponse({'status': 'error', 'message': 'Attendance window is closed.'}, status=400)

            # 3. Find Student by their student_id
            try:
                student = Student.objects.get(student_id=student_id_str)
            except Student.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': f'Student ID {student_id_str} not found.'}, status=404)

            # 4. Check if student is enrolled
            if not Enrollment.objects.filter(student=student, class_obj=class_obj).exists():
                return JsonResponse({'status': 'error', 'message': f'{student.user.get_full_name()} is not enrolled in this class.'}, status=400)

            # 5. Mark Attendance
            today = timezone.now().date()
            attendance_record, created = Attendance.objects.update_or_create(
                student=student,
                class_obj=class_obj,
                date=today,
                defaults={'status': 'P', 'timestamp': timezone.now()}
            )
            
            message = f"Success: {student.user.get_full_name()} marked 'Present'."
            if not created and attendance_record.status == 'P':
                 message = f"Already marked 'Present': {student.user.get_full_name()}."

            return JsonResponse({'status': 'success', 'message': message})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# --- Student Views ---

class StudentDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Dashboard for Students.
    """
    def test_func(self):
        return is_student(self.request.user)

    def get(self, request, *args, **kwargs):
        student = request.user.student
        now = timezone.now()
        
        # Get all enrolled classes
        enrolled_classes = Class.objects.filter(enrollments__student=student).order_by('start_time')
        
        # Dashboard stats
        current_classes = enrolled_classes.filter(start_time__lte=now.time(), end_time__gte=now.time())
        upcoming_classes = enrolled_classes.filter(start_time__gt=now.time())
        
        # Attendance Performance
        total_attendance = Attendance.objects.filter(student=student).count()
        present_attendance = Attendance.objects.filter(student=student, status='P').count()
        
        if total_attendance > 0:
            attendance_percent = (present_attendance / total_attendance) * 100
        else:
            attendance_percent = 100 # Default to 100 if no records yet

        context = {
            'enrolled_classes': enrolled_classes,
            'current_classes': current_classes,
            'upcoming_classes': upcoming_classes,
            'attendance_percent': round(attendance_percent, 2),
            'total_attendance': total_attendance,
            'present_attendance': present_attendance,
        }
        return render(request, 'student_dashboard.html', context)

class StudentAttendanceHistoryView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Student: View attendance history for a specific class.
    """
    def test_func(self):
        return is_student(self.request.user)
    
    def get(self, request, class_id, *args, **kwargs):
        student = request.user.student
        
        # Check if student is enrolled in this class
        class_obj = get_object_or_404(Class, id=class_id)
        if not Enrollment.objects.filter(student=student, class_obj=class_obj).exists():
            messages.error(request, "You are not enrolled in this class.")
            return redirect('student_dashboard')

        # Get attendance history for this class
        history = Attendance.objects.filter(
            student=student, 
            class_obj=class_obj
        ).order_by('-date')
        
        context = {
            'class_obj': class_obj,
            'history': history,
        }
        return render(request, 'attendance_history.html', context)