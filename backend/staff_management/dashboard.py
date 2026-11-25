from django.urls import reverse
from django.db.models import Q
from core.dashboard import badge, format_money
from .models import StaffMember


def staff_section(request=None):
    staff_members = StaffMember.objects.select_related('user__account_profile').all().order_by('-created_at')
    
    search_query = ''
    status_filter = ''
    department_filter = ''
    
    if request:
        search_query = request.GET.get('search', '')
        if search_query:
            staff_members = staff_members.filter(
                Q(staff_id__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(position__icontains=search_query)
            )
        
        status_filter = request.GET.get('status', '')
        if status_filter:
            staff_members = staff_members.filter(employment_status=status_filter)
        
        department_filter = request.GET.get('department', '')
        if department_filter:
            staff_members = staff_members.filter(department__icontains=department_filter)
    
    rows = []
    for staff in staff_members[:50]:
        if staff.user:
            user_name = staff.user.get_full_name() or staff.user.username
            user_status = 'Active' if staff.user.is_active else 'Inactive'
            user_status_badge = badge(user_status, 'success' if staff.user.is_active else 'danger')
            phone = staff.user.account_profile.phone if hasattr(staff.user, 'account_profile') and staff.user.account_profile.phone else '-'
            email = staff.user.email or '-'
        else:
            user_name = '<span class="text-danger">No User Linked</span>'
            user_status_badge = badge('No User', 'danger')
            phone = '-'
            email = '-'
        
        rows.append({
            'view_url': reverse('staff_detail', args=[staff.pk]),
            'edit_url': reverse('staff_update', args=[staff.pk]),
            'delete_url': reverse('staff_delete', args=[staff.pk]),
            'cells': [
                staff.staff_id,
                user_name,
                staff.user.username if staff.user else '-',
                staff.position,
                staff.department,
                staff.get_shift_display(),
                format_money(staff.salary),
                staff.joining_date,
                staff.experience or '-',
                staff.qualification or '-',
                phone,
                email,
                user_status_badge,
                badge(staff.get_employment_status_display(), 'success' if staff.employment_status == 'active' else 'warning'),
            ],
        })
    
    departments = StaffMember.objects.values_list('department', flat=True).distinct()
    status_choices = StaffMember.STATUS_CHOICES
    
    return {
        'id': 'staff',
        'title': 'Staff & HR Management',
        'icon': 'bi bi-person-badge',
        'action_label': 'Add Staff',
        'action_url': reverse('staff_create'),
        'empty_message': 'No staff records found.',
        'headings': ['ID', 'Name', 'Username', 'Position', 'Department', 'Shift', 'Salary', 'Joining Date', 'Experience', 'Qualification', 'Phone', 'Email', 'User Status', 'Employment Status'],
        'rows': rows,
        'filters': {
            'search': search_query,
            'status': status_filter,
            'department': department_filter,
            'departments': departments,
            'status_choices': status_choices,
        }
    }


def stats():
    return {
        'active_staff': StaffMember.objects.filter(employment_status='active').count(),
        'total_staff': StaffMember.objects.count(),
        'probation_staff': StaffMember.objects.filter(employment_status='probation').count(),
        'inactive_staff': StaffMember.objects.filter(employment_status='inactive').count(),
    }