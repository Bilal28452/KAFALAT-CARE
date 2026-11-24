from django.contrib import admin
from .models import StaffMember


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