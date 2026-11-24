from django.urls import path
from accounts.views import (
    index, register, user_login, user_logout, dashboard,
    user_list, user_create, user_detail, user_update, user_delete,
    user_profile, user_change_password,
    donor_login, donor_signup, donor_logout, donor_dashboard,
    donor_donation_create, donor_donation_list, donor_donation_detail,
    donor_profile, donor_change_password,
    sponsor_login, sponsor_signup, sponsor_logout, sponsor_dashboard,
    sponsor_child_detail, sponsor_application, sponsor_profile,
    sponsor_change_password
)

urlpatterns = [
    # Authentication URLs
    path('', index, name='index'),
    path('admin_signup/', register, name='admin_signup'),
    path('admin_login/', user_login, name='admin_login'),
    path('login/', user_login, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', user_logout, name='logout'),

    # User Management URLs
    path('users/', user_list, name='user_list'),
    path('users/add/', user_create, name='user_create'),
    path('users/<int:pk>/', user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', user_update, name='user_update'),
    path('users/<int:pk>/delete/', user_delete, name='user_delete'),
    
    # Profile URLs
    path('profile/', user_profile, name='user_profile'),
    path('profile/change-password/', user_change_password, name='user_change_password'),

    # Donor Authentication and Dashboard URLs
    path('donor/login/', donor_login, name='donor_login'),
    path('donor/signup/', donor_signup, name='donor_signup'),
    path('donor/logout/', donor_logout, name='donor_logout'),
    path('donor/dashboard/', donor_dashboard, name='donor_dashboard'),

    # Donor Donation URLs
    path('donor/donations/', donor_donation_list, name='donor_donation_list'),
    path('donor/donations/create/', donor_donation_create, name='donor_donation_create'),
    path('donor/donations/<int:pk>/', donor_donation_detail, name='donor_donation_detail'),

    # Donor Profile URLs
    path('donor/profile/', donor_profile, name='donor_profile'),
    path('donor/profile/change-password/', donor_change_password, name='donor_change_password'),

    # Sponsor Authentication and Dashboard URLs
    path('sponsor/login/', sponsor_login, name='sponsor_login'),
    path('sponsor/signup/', sponsor_signup, name='sponsor_signup'),
    path('sponsor/logout/', sponsor_logout, name='sponsor_logout'),
    path('sponsor/dashboard/', sponsor_dashboard, name='sponsor_dashboard'),
    path('sponsor/children/<int:pk>/', sponsor_child_detail, name='sponsor_child_detail'),
    path('sponsor/application/', sponsor_application, name='sponsor_application'),
    path('sponsor/profile/', sponsor_profile, name='sponsor_profile'),
    path('sponsor/profile/change-password/', sponsor_change_password, name='sponsor_change_password'),
]