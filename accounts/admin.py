from django.contrib import admin
from .models import AccountProfile, AuditLog


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'cnic', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'phone', 'cnic')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'user_role', 'action', 'module', 'status', 'ip_address')
    list_filter = ('status', 'module', 'action', 'created_at')
    search_fields = ('user__username', 'user__email', 'action', 'module', 'record_id', 'details')
    readonly_fields = ('created_at',)
