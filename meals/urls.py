from django.urls import path
from .views import meal_views, schedule_views, report_views

urlpatterns = [
    # Daily Log
    path('daily-log/', meal_views.daily_log, name='daily_log'),
    path('allergy/<int:child_id>/', meal_views.child_allergy_update, name='child_allergy_update'),
    
    # Meal Schedule
    path('schedule/', schedule_views.meal_schedule, name='meal_schedule'),
    path('schedule/create/', schedule_views.meal_schedule_create, name='meal_schedule_create'),
    path('schedule/<int:pk>/edit/', schedule_views.meal_schedule_edit, name='meal_schedule_edit'),
    path('schedule/<int:pk>/delete/', schedule_views.meal_schedule_delete, name='meal_schedule_delete'),
    
    # Reports
    path('reports/', report_views.meal_reports, name='meal_reports'),
]