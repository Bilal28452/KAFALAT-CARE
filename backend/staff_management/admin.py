from django.contrib import admin
from .models import CareIncident, DailyCareLog, StaffMember


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'get_user_name', 'position', 'department', 'shift', 'employment_status')
    list_filter = ('department', 'shift', 'employment_status', 'joining_date')
    search_fields = ('staff_id', 'user__first_name', 'user__last_name', 'user__username', 'position')
    
    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return 'No User Linked'
    get_user_name.short_description = 'Full Name'


@admin.register(DailyCareLog)
class DailyCareLogAdmin(admin.ModelAdmin):
    list_display = ('child', 'date', 'shift', 'caretaker', 'hygiene_status', 'rest_status', 'mood')
    list_filter = ('date', 'shift', 'hygiene_status', 'rest_status', 'mood')
    search_fields = ('child__full_name', 'child__child_id', 'caretaker__staff_id')


@admin.register(CareIncident)
class CareIncidentAdmin(admin.ModelAdmin):
    list_display = ('child', 'category', 'severity', 'status', 'reported_by', 'created_at')
    list_filter = ('category', 'severity', 'status', 'created_at')
    search_fields = ('child__full_name', 'child__child_id', 'description')
    readonly_fields = ('reported_by', 'created_at', 'updated_at')