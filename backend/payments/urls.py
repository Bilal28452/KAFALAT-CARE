from django.urls import path

from . import views


urlpatterns = [
    path('webhook/', views.safepay_webhook, name='safepay_webhook'),
    path('return/', views.payment_return, name='payment_return'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('donations/<int:donation_id>/checkout/', views.donation_checkout, name='donation_checkout'),
    path('sponsorships/<int:sponsorship_id>/checkout/', views.sponsorship_checkout, name='sponsorship_checkout'),
]
