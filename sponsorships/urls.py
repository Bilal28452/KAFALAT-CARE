from django.urls import path
from . import views

urlpatterns = [
    path('', views.sponsorship_list, name='sponsorship_list'),
    path('create/', views.sponsorship_create, name='sponsorship_create'),
    path('<int:pk>/', views.sponsorship_detail, name='sponsorship_detail'),
    path('<int:pk>/edit/', views.sponsorship_update, name='sponsorship_update'),
    path('<int:pk>/delete/', views.sponsorship_delete, name='sponsorship_delete'),
    path('<int:pk>/approve/', views.sponsorship_approve, name='sponsorship_approve'),
    path('<int:pk>/reject/', views.sponsorship_reject, name='sponsorship_reject'),
]
