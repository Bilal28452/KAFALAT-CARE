from django.urls import path
from .views import staff_views, attendance_views, payroll_views, leave_views

urlpatterns = [
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