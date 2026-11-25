from django.contrib.auth import get_user_model
from django.urls import reverse

from core.dashboard import badge
from staff_management.models import StaffMember

from .models import AccountProfile, AuditLog


def users_section():
    rows = []
    profiles = AccountProfile.objects.select_related('user').order_by('-created_at')[:50]
    for profile in profiles:
        user = profile.user
        rows.append({
            'view_url': reverse('admin:auth_user_change', args=[user.pk]),
            'edit_url': reverse('admin:auth_user_change', args=[user.pk]),
            'delete_url': reverse('user_delete', args=[user.pk]),
            'delete_label': f'user {user.username}',
            'cells': [
                user.username,
                user.get_full_name() or user.username,
                user.email,
                badge(profile.get_role_display(), 'info'),
                profile.phone,
                badge('Active' if user.is_active else 'Inactive', 'success' if user.is_active else 'danger'),
                user.last_login or 'Never',
                profile.cnic,
                profile.created_at.date(),
            ],
        })

    return {
        'id': 'users',
        'title': 'User Management',
        'icon': 'bi bi-shield-lock',
        'action_label': 'Add User',
        'action_url': reverse('admin:auth_user_add'),
        'empty_message': 'No user profiles found.',
        'headings': ['Username', 'Full Name', 'Email', 'Role', 'Phone', 'Status', 'Last Login', 'CNIC', 'Created At'],
        'rows': rows,
    }


def staff_section():
    """Staff section for admin dashboard"""
    staff_members = StaffMember.objects.all().order_by('-created_at')[:50]
    
    rows = []
    for staff in staff_members:
        # Status badge
        if staff.status == 'active':
            status_badge = badge('Active', 'success')
        elif staff.status == 'probation':
            status_badge = badge('Probation', 'warning')
        else:
            status_badge = badge('Inactive', 'danger')
        
        rows.append({
            'view_url': reverse('staff_detail', args=[staff.pk]),
            'edit_url': reverse('staff_update', args=[staff.pk]),
            'cells': [
                staff.staff_id,
                staff.full_name,
                staff.position,
                staff.department,
                staff.get_shift_display(),
                f'PKR {staff.salary:,.0f}',
                staff.phone or '-',
                status_badge,
            ],
        })
    
    return {
        'id': 'staff',
        'title': 'Staff Management',
        'icon': 'bi bi-person-badge',
        'action_label': 'Add Staff',
        'action_url': reverse('staff_create'),
        'empty_message': 'No staff members found.',
        'headings': ['Staff ID', 'Full Name', 'Position', 'Department', 'Shift', 'Salary', 'Phone', 'Status'],
        'rows': rows,
    }


def audit_section():
    rows = []
    for log in AuditLog.objects.select_related('user')[:50]:
        rows.append({
            'view_url': reverse('admin:accounts_auditlog_change', args=[log.pk]),
            'edit_url': reverse('admin:accounts_auditlog_change', args=[log.pk]),
            'delete_url': reverse('admin:accounts_auditlog_delete', args=[log.pk]),
            'delete_label': f'audit log #{log.pk}',
            'cells': [
                log.created_at,
                log.user.get_username() if log.user else 'System',
                log.user_role,
                log.action,
                log.module,
                log.record_id or 'N/A',
                log.ip_address or '',
                log.user_agent[:60],
                badge(log.get_status_display(), 'info' if log.status == AuditLog.STATUS_SUCCESS else 'danger'),
                log.details,
            ],
        })

    return {
        'id': 'audit',
        'title': 'Audit Logs',
        'icon': 'bi bi-file-earmark-text',
        'action_label': '',
        'empty_message': 'No audit logs found yet.',
        'headings': ['Timestamp', 'User', 'User Role', 'Action', 'Module', 'Record ID', 'IP Address', 'User Agent', 'Status', 'Details'],
        'rows': rows,
    }


def user_stats():
    User = get_user_model()
    return {
        'total_users': User.objects.count(),
        'admins': AccountProfile.objects.filter(role=AccountProfile.ROLE_ADMIN).count(),
    }


def staff_stats():
    """Staff statistics for dashboard"""
    return {
        'active_staff': StaffMember.objects.filter(status='active').count(),
        'total_staff': StaffMember.objects.count(),
        'probation_staff': StaffMember.objects.filter(status='probation').count(),
    }


def record_audit_log(request, action, module, details='', record_id='', status=AuditLog.STATUS_SUCCESS):
    profile = getattr(request.user, 'account_profile', None)
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        user_role=profile.get_role_display() if profile else '',
        action=action,
        module=module,
        record_id=record_id,
        ip_address=request.META.get('REMOTE_ADDR') or None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        status=status,
        details=details,
    )