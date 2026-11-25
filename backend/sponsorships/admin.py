from django.contrib import admin

from .models import Sponsorship


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ('sponsor_code', 'sponsor_name', 'child', 'monthly_amount', 'start_date', 'status', 'ai_match_score')
    list_filter = ('status', 'start_date', 'payment_method')
    search_fields = ('sponsor_code', 'sponsor_name', 'cnic', 'phone', 'email', 'child__full_name')
