from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q

from accounts.views import is_admin_user
from accounts.dashboard import record_audit_log
from staff_management.models import StaffMember


@login_required(login_url='admin_login')
def teacher_list(request):
    """List all staff members who are teachers (position contains 'Teacher')"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    # Filter staff members who are teachers
    teachers = StaffMember.objects.filter(
        position__icontains='Teacher'
    ).select_related('user').order_by('staff_id')
    
    search_query = request.GET.get('search', '')
    if search_query:
        teachers = teachers.filter(
            Q(staff_id__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(position__icontains=search_query) |
            Q(department__icontains=search_query)
        )
    
    record_audit_log(request, 'VIEW', 'Teachers', details='Viewed teachers list')
    
    context = {
        'teachers': teachers,
        'search_query': search_query,
        'section': 'education'
    }
    return render(request, 'children/teacher_list.html', context)


@login_required(login_url='admin_login')
def teacher_detail(request, pk):
    """View teacher details"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    teacher = get_object_or_404(StaffMember.objects.select_related('user'), pk=pk)
    
    # Verify this staff member is actually a teacher
    if 'Teacher' not in teacher.position:
        messages.warning(request, 'This staff member is not marked as a teacher.')
    
    record_audit_log(
        request, 'VIEW', 'Teachers',
        record_id=teacher.staff_id,
        details=f'Viewed teacher: {teacher.user.get_full_name() if teacher.user else teacher.staff_id}'
    )
    
    context = {
        'teacher': teacher,
        'section': 'education'
    }
    return render(request, 'children/teacher_detail.html', context)


@login_required(login_url='admin_login')
def teacher_update(request, pk):
    """Update teacher information (redirect to staff update)"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    teacher = get_object_or_404(StaffMember, pk=pk)
    
    # Redirect to staff update page
    messages.info(request, f'Edit teacher information in Staff Management: {teacher.staff_id}')
    return redirect('staff_update', pk=teacher.pk)


@login_required(login_url='admin_login')
def teacher_delete(request, pk):
    """Delete teacher (redirect to staff delete)"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    teacher = get_object_or_404(StaffMember, pk=pk)
    
    messages.warning(request, f'To delete a teacher, please go to Staff Management section.')
    return redirect('staff_list')