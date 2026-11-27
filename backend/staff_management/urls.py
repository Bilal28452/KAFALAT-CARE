from django.urls import path
from .views import (
    staff_views,
    attendance_views,
    payroll_views,
    leave_views,
    teacher_views,
    doctor_views,
    caretaker_views,
)

urlpatterns = [
    # Staff workspaces
    path('doctor/dashboard/', doctor_views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/patients/', doctor_views.doctor_patients, name='doctor_patients'),
    path('doctor/incidents/', doctor_views.doctor_incidents, name='doctor_incidents'),
    path('doctor/incidents/<int:pk>/review/', doctor_views.doctor_incident_review, name='doctor_incident_review'),
    path('doctor/patients/<int:pk>/', doctor_views.doctor_patient_detail, name='doctor_patient_detail'),
    path('doctor/patients/<int:pk>/health/add/', doctor_views.doctor_health_record_create, name='doctor_health_record_create'),
    path('doctor/health/<int:pk>/edit/', doctor_views.doctor_health_record_update, name='doctor_health_record_update'),
    path('caretaker/dashboard/', caretaker_views.caretaker_dashboard, name='caretaker_dashboard'),
    path('caretaker/children/', caretaker_views.caretaker_children, name='caretaker_children'),
    path('caretaker/children/<int:pk>/care/', caretaker_views.caretaker_daily_care, name='caretaker_daily_care'),
    path('caretaker/children/<int:pk>/incidents/report/', caretaker_views.caretaker_incident_report, name='caretaker_incident_report'),
    path('caretaker/incidents/', caretaker_views.caretaker_incidents, name='caretaker_incidents'),
    path('caretaker/education/', caretaker_views.caretaker_education_tracking, name='caretaker_education_tracking'),
    path('caretaker/health/', caretaker_views.caretaker_health_tracking, name='caretaker_health_tracking'),
    path('caretaker/messages/', caretaker_views.caretaker_messages, name='caretaker_messages'),
    path('caretaker/children/<int:pk>/meals/', caretaker_views.caretaker_meal_log, name='caretaker_meal_log'),
    path('teacher/dashboard/', teacher_views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/students/', teacher_views.teacher_students, name='teacher_students'),
    path('teacher/attendance/', teacher_views.teacher_attendance, name='teacher_attendance'),
    path('teacher/results/', teacher_views.teacher_results, name='teacher_results'),
    path('teacher/results/add/', teacher_views.teacher_result_create, name='teacher_result_create'),
    path('teacher/results/<int:pk>/edit/', teacher_views.teacher_result_update, name='teacher_result_update'),

    # Staff CRUD
    path('', staff_views.staff_list, name='staff_list'),
    path('add/', staff_views.staff_create, name='staff_create'),
    path('<int:pk>/', staff_views.staff_detail, name='staff_detail'),
    path('<int:pk>/edit/', staff_views.staff_update, name='staff_update'),
    path('<int:pk>/delete/', staff_views.staff_delete, name='staff_delete'),
    
    # Attendance
    path('attendance/', attendance_views.staff_attendance, name='staff_attendance'),
    
    # Payroll
    path('payroll/', payroll_views.staff_payroll, name='staff_payroll'),
    path('payroll/create/', payroll_views.staff_payroll_create, name='staff_payroll_create'),
    path('payroll/<int:pk>/edit/', payroll_views.staff_payroll_edit, name='staff_payroll_edit'),
    
    # Leave Requests
    path('leaves/', leave_views.staff_leaves, name='staff_leaves'),
    path('leaves/create/', leave_views.staff_leave_create, name='staff_leave_create'),
    path('leaves/<int:pk>/approve/', leave_views.staff_leave_approve, name='staff_leave_approve'),
    path('leaves/<int:pk>/reject/', leave_views.staff_leave_reject, name='staff_leave_reject'),
    path('leaves/update/<int:pk>/', leave_views.staff_leave_update, name='staff_leave_update'),
    path('leaves/delete/<int:pk>/', leave_views.staff_leave_delete, name='staff_leave_delete'),
    path('leaves/bulk-action/', leave_views.staff_leave_bulk_action, name='staff_leave_bulk_action'),
]