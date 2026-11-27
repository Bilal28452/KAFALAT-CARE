from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from sponsorships import views as sponsorship_views
from accounts.views import (
    index, register, user_login, user_logout, dashboard,
    user_list, user_create, user_detail, user_update, user_delete,
    user_profile, user_change_password,
    donor_login, donor_signup, donor_logout, donor_dashboard,
    donor_donation_create, donor_donation_list, donor_donation_detail,
    donor_profile, donor_change_password,
    sponsor_login, sponsor_signup, sponsor_logout, sponsor_dashboard,
    sponsor_child_detail, sponsor_application, sponsor_profile,
    sponsor_change_password, sponsor_health_tracking,
    sponsor_education_tracking, sponsor_meal_tracking,
)

urlpatterns = [
    # Authentication URLs
    path('', index, name='index'),
    path('admin_signup/', register, name='admin_signup'),
    path('admin_login/', user_login, name='admin_login'),
    path('login/', user_login, name='login'),
    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        email_template_name='accounts/password_reset_email.txt',
        html_email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),
    path('forgot-password/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),
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
    path('sponsor/messages/', sponsorship_views.sponsorship_message_inbox, name='sponsor_message_inbox'),
    path('sponsor/messages/<int:conversation_id>/', sponsorship_views.sponsorship_message_thread, name='sponsor_message_thread'),
    path('sponsor/children/<int:pk>/', sponsor_child_detail, name='sponsor_child_detail'),
    path('sponsor/children/<int:pk>/health/', sponsor_health_tracking, name='sponsor_health_tracking'),
    path('sponsor/children/<int:pk>/education/', sponsor_education_tracking, name='sponsor_education_tracking'),
    path('sponsor/children/<int:pk>/meals/', sponsor_meal_tracking, name='sponsor_meal_tracking'),
    path('sponsor/application/', sponsor_application, name='sponsor_application'),
    path('sponsor/profile/', sponsor_profile, name='sponsor_profile'),
    path('sponsor/profile/change-password/', sponsor_change_password, name='sponsor_change_password'),
]
