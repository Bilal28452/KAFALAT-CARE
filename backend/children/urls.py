from django.urls import path
from . import views

urlpatterns = [
    # Child URLs
    path('', views.child_list, name='child_list'),
    path('add/', views.child_create, name='child_create'),
    path('<int:pk>/', views.child_detail, name='child_detail'),
    path('<int:pk>/edit/', views.child_update, name='child_update'),
    path('<int:pk>/delete/', views.child_delete, name='child_delete'),
    path('<int:pk>/health-timeline/', views.child_health_timeline, name='child_health_timeline'),
    path('<int:pk>/health-pattern/analyze/', views.analyze_child_health_patterns, name='health_pattern_analyze'),
    
    # Health Record URLs
    path('health/add/', views.health_record_create, name='health_record_create'),
    path('health/<int:pk>/', views.health_record_detail, name='health_record_detail'),
    path('health/<int:pk>/edit/', views.health_record_update, name='health_record_update'),
    path('health/<int:pk>/delete/', views.health_record_delete, name='health_record_delete'),
    
    # Education Record URLs
    path('education/', views.education_record_list, name='education_record_list'),
    path('education/add/', views.education_record_create, name='education_record_create'),
    path('education/<int:pk>/', views.education_record_detail, name='education_record_detail'),
    path('education/<int:pk>/edit/', views.education_record_update, name='education_record_update'),
    path('education/<int:pk>/delete/', views.education_record_delete, name='education_record_delete'),
    
    # Education Dashboard
    path('education/dashboard/', views.education_dashboard, name='education_dashboard'),
    path('education/class-overview/', views.education_class_overview, name='education_class_overview'),
    path('attendance/', views.education_attendance, name='attendance'),
    
    # Course URLs
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_create, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_update, name='course_update'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    

   # Teacher URLs (viewing teachers from Staff)
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('teachers/<int:pk>/edit/', views.teacher_update, name='teacher_update'),
    path('teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'), 


    # Education Result URLs
    path('results/', views.education_result_list, name='education_result_list'),
    path('results/add/', views.education_result_create, name='education_result_create'),
    path('results/<int:pk>/', views.education_result_detail, name='education_result_detail'),
    path('results/<int:pk>/edit/', views.education_result_update, name='education_result_update'),
    path('results/<int:pk>/delete/', views.education_result_delete, name='education_result_delete'),
]