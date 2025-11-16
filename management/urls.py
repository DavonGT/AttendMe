from django.urls import path
from . import views

urlpatterns = [
    # Main Dashboard (redirects)
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Teacher URLs
    path('teacher/dashboard/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('teacher/class/create/', views.ClassCreateView.as_view(), name='class_create'),
    path('teacher/class/<int:pk>/update/', views.ClassUpdateView.as_view(), name='class_update'),
    path('teacher/class/<int:class_id>/enroll/', views.ManageEnrollmentsView.as_view(), name='manage_enrollments'),
    path('teacher/class/<int:class_id>/attendance/', views.MarkAttendanceView.as_view(), name='mark_attendance'),
    path('teacher/class/<int:class_id>/history/', views.TeacherAttendanceHistoryView.as_view(), name='teacher_attendance_history'),
    
    # Teacher Scanner URLs
    path('teacher/class/<int:class_id>/scan/', views.ScannerAttendanceView.as_view(), name='scan_attendance'),
    path('api/mark-attendance/', views.MarkAttendanceAPIView.as_view(), name='api_mark_attendance'),

    # Student URLs
    path('student/dashboard/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('student/attendance/<int:class_id>/', views.StudentAttendanceHistoryView.as_view(), name='student_attendance_history'),
]