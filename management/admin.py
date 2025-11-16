from django.contrib import admin
from .models import Teacher, Student, Class, Enrollment, Attendance

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'start_time', 'end_time', 'enrolled_student_count')
    list_filter = ('teacher',)
    search_fields = ('name', 'teacher__user__username')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_obj')
    list_filter = ('class_obj',)
    search_fields = ('student__user__username', 'class_obj__name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_obj', 'date', 'status')
    list_filter = ('class_obj', 'date', 'status')
    search_fields = ('student__user__username', 'class_obj__name')