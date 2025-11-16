from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Model to link a Django User to a Teacher profile
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, null=True, blank=True)
    middle_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Employee ID")

    @property
    def full_name(self):
        names = [self.first_name, self.middle_name[0] if self.middle_name else '', self.last_name]
        return ' '.join(name for name in names if name)
    
    def __str__(self):
        return self.full_name or self.user.get_full_name() or self.user.username or self.employee_id

# Model to link a Django User to a Student profile
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, null=True, blank=True)
    middle_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Student ID")
    
    @property
    def full_name(self):
        names = [self.first_name, self.middle_name[0] if self.middle_name else '', self.last_name]
        return ' '.join(name for name in names if name)

    def __str__(self):
        return self.full_name or self.user.get_full_name() or self.user.username or self.student_id

# Model for a Class
class Class(models.Model):
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='classes')
    start_time = models.TimeField()
    end_time = models.TimeField()
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.teacher})"
    
    @property
    def is_active_now(self):
        """
        Helper property to check if the class is currently in session.
        """
        now = timezone.now().time()
        return self.start_time <= now <= self.end_time

    @property
    def enrolled_student_count(self):
        """
        Helper property to get the count of enrolled students.
        """
        return self.enrollments.count()

# Model for Student Enrollment in a Class
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='enrollments', verbose_name="Class")
    
    class Meta:
        # Ensures a student can only enroll in a class once
        unique_together = ('student', 'class_obj')

    def __str__(self):
        return f"{self.student} enrolled in {self.class_obj}"

# Model for Attendance
class Attendance(models.Model):
    STATUS_CHOICES = (
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Late'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendance', verbose_name="Class")
    date = models.DateField(default=timezone.now)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    
    class Meta:
        # A student can only have one attendance record per class per day
        unique_together = ('student', 'class_obj', 'date')
        ordering = ['-date', 'class_obj']

    def __str__(self):
        return f"{self.student} - {self.class_obj} on {self.date}: {self.get_status_display()}"