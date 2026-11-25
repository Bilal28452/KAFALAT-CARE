from django.urls import path
from . import views

urlpatterns = [
    path('', views.sponsorship_list, name='sponsorship_list'),
    path('messages/', views.sponsorship_message_inbox, name='sponsorship_message_inbox'),
    path('messages/<int:conversation_id>/', views.sponsorship_message_thread, name='sponsorship_message_thread'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('children/<int:child_id>/message/', views.sponsor_message_send, name='sponsor_message_send'),
    path('<int:pk>/cancel/', views.sponsor_cancel_sponsorship, name='sponsor_cancel_sponsorship'),
    path('create/', views.sponsorship_create, name='sponsorship_create'),
    path('<int:pk>/', views.sponsorship_detail, name='sponsorship_detail'),
    path('<int:pk>/edit/', views.sponsorship_update, name='sponsorship_update'),
    path('<int:pk>/delete/', views.sponsorship_delete, name='sponsorship_delete'),
    path('<int:pk>/approve/', views.sponsorship_approve, name='sponsorship_approve'),
    path('<int:pk>/reject/', views.sponsorship_reject, name='sponsorship_reject'),
]
