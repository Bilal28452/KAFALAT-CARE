from django.urls import path
from . import views

urlpatterns = [
    path('', views.donation_list, name='donation_list'),
    path('create/', views.donation_create, name='donation_create'),
    path('<int:pk>/', views.donation_detail, name='donation_detail'),
    path('<int:pk>/edit/', views.donation_update, name='donation_update'),
    path('<int:pk>/delete/', views.donation_delete, name='donation_delete'),
]
