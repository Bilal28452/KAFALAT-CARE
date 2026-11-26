from django.contrib import admin

from .models import Payment, PaymentWebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'reference',
        'purpose',
        'amount',
        'currency',
        'status',
        'tracker_token',
        'created_at',
        'paid_at',
    )
    list_filter = ('purpose', 'status', 'currency', 'created_at')
    search_fields = (
        'reference',
        'tracker_token',
        'donation__donor_name',
        'sponsorship__sponsor_name',
    )
    readonly_fields = tuple(field.name for field in Payment._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ('event_token', 'event_type', 'received_at', 'processed')
    list_filter = ('event_type', 'processed', 'received_at')
    search_fields = ('event_token', 'event_type')
    readonly_fields = ('event_token', 'event_type', 'received_at', 'processed')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
