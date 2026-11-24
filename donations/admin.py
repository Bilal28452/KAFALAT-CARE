from django.contrib import admin

from .models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor_name', 'donor_type', 'amount', 'donation_type', 'donated_at', 'status')
    list_filter = ('donor_type', 'donation_type', 'status', 'donated_at')
    search_fields = ('donor_name', 'transaction_id', 'receipt_number', 'allocated_to')
