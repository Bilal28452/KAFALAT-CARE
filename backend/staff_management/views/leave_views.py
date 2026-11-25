from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime

from accounts.views.auth_views import is_admin_user
from accounts.dashboard import record_audit_log
from ..models import StaffMember, LeaveRequest


@login_required(login_url='admin_login')
def staff_leaves(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    leave_type_filter = request.GET.get('leave_type', '')
    staff_search = request.GET.get('staff_search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    leaves = LeaveRequest.objects.select_related('staff', 'approved_by').all()
    
    # Apply filters
    if status_filter:
        leaves = leaves.filter(status=status_filter)
    
    if leave_type_filter:
        leaves = leaves.filter(leave_type=leave_type_filter)
    
    if staff_search:
        leaves = leaves.filter(
            Q(staff__staff_id__icontains=staff_search) |
            Q(staff__user__first_name__icontains=staff_search) |
            Q(staff__user__last_name__icontains=staff_search) |
            Q(staff__user__username__icontains=staff_search)
        )
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            leaves = leaves.filter(start_date__gte=date_from_obj)
        except:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            leaves = leaves.filter(end_date__lte=date_to_obj)
        except:
            pass
    
    # Get all staff for filter dropdown
    staff_members = StaffMember.objects.filter(employment_status='active')
    
    # Statistics
    total_leaves = leaves.count()
    pending_count = LeaveRequest.objects.filter(status='pending').count()
    approved_count = LeaveRequest.objects.filter(status='approved').count()
    rejected_count = LeaveRequest.objects.filter(status='rejected').count()
    
    context = {
        'leaves': leaves.order_by('-created_at'),
        'status_filter': status_filter,
        'leave_type_filter': leave_type_filter,
        'staff_search': staff_search,
        'date_from': date_from,
        'date_to': date_to,
        'staff_members': staff_members,
        'leave_types': LeaveRequest.LEAVE_TYPES,
        'total_leaves': total_leaves,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'section': 'staff'
    }
    return render(request, 'staff_management/staff_leaves.html', context)


@login_required(login_url='admin_login')
def staff_leave_create(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        staff_id = request.POST.get('staff')
        leave_type = request.POST.get('leave_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')
        
        staff = get_object_or_404(StaffMember, pk=staff_id)
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Check for overlapping leave requests
        overlapping = LeaveRequest.objects.filter(
            staff=staff,
            status__in=['pending', 'approved'],
            start_date__lte=end,
            end_date__gte=start
        ).exists()
        
        if overlapping:
            messages.error(request, 'This staff member already has a leave request for this period.')
            return redirect('staff_leave_create')
        
        LeaveRequest.objects.create(
            staff=staff,
            leave_type=leave_type,
            start_date=start,
            end_date=end,
            reason=reason
        )
        messages.success(request, f'Leave request submitted for {staff.user.get_full_name()}.')
        return redirect('staff_leaves')
    
    staff_members = StaffMember.objects.filter(employment_status='active')
    context = {
        'staff_members': staff_members,
        'leave_types': LeaveRequest.LEAVE_TYPES,
        'section': 'staff'
    }
    return render(request, 'staff_management/staff_leave_form.html', context)


@login_required(login_url='admin_login')
def staff_leave_approve(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    leave = get_object_or_404(LeaveRequest, pk=pk)
    
    if leave.status == 'approved':
        messages.warning(request, 'This leave request is already approved.')
    else:
        leave.status = 'approved'
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()
        messages.success(request, f'Leave request approved for {leave.staff.user.get_full_name()}.')
    
    return redirect('staff_leaves')


@login_required(login_url='admin_login')
def staff_leave_reject(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    leave = get_object_or_404(LeaveRequest, pk=pk)
    
    if leave.status == 'rejected':
        messages.warning(request, 'This leave request is already rejected.')
    else:
        leave.status = 'rejected'
        leave.save()
        messages.success(request, f'Leave request rejected for {leave.staff.user.get_full_name()}.')
    
    return redirect('staff_leaves')


@login_required(login_url='admin_login')
def staff_leave_update(request, pk):
    """Edit leave request (even if approved/rejected)"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    leave = get_object_or_404(LeaveRequest, pk=pk)
    
    if request.method == 'POST':
        leave.leave_type = request.POST.get('leave_type')
        leave.start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()
        leave.end_date = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d').date()
        leave.reason = request.POST.get('reason')
        leave.status = request.POST.get('status')
        
        if leave.status == 'approved' and not leave.approved_by:
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
        
        leave.save()
        messages.success(request, 'Leave request updated successfully.')
        return redirect('staff_leaves')
    
    context = {
        'leave': leave,
        'staff_members': StaffMember.objects.filter(employment_status='active'),
        'leave_types': LeaveRequest.LEAVE_TYPES,
        'section': 'staff'
    }
    return render(request, 'staff_management/staff_leave_form.html', context)


@login_required(login_url='admin_login')
def staff_leave_delete(request, pk):
    """Delete leave request (with confirmation)"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    leave = get_object_or_404(LeaveRequest, pk=pk)
    
    if request.method == 'POST':
        staff_name = leave.staff.user.get_full_name() or leave.staff.user.username
        leave.delete()
        messages.success(request, f'Leave request for {staff_name} has been deleted.')
        return redirect('staff_leaves')
    
    context = {
        'leave': leave,
        'section': 'staff'
    }
    return render(request, 'staff_management/staff_leave_confirm_delete.html', context)


@login_required(login_url='admin_login')
def staff_leave_bulk_action(request):
    """Bulk approve/reject multiple leave requests"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        leave_ids = request.POST.getlist('leave_ids')
        action = request.POST.get('action')
        
        if not leave_ids:
            messages.warning(request, 'No leave requests selected.')
            return redirect('staff_leaves')
        
        leaves = LeaveRequest.objects.filter(pk__in=leave_ids)
        
        if action == 'approve':
            count = leaves.update(status='approved', approved_by=request.user, approved_at=timezone.now())
            messages.success(request, f'{count} leave request(s) approved.')
        elif action == 'reject':
            count = leaves.update(status='rejected')
            messages.success(request, f'{count} leave request(s) rejected.')
        elif action == 'delete':
            count = leaves.count()
            leaves.delete()
            messages.success(request, f'{count} leave request(s) deleted.')
        
        return redirect('staff_leaves')
    
    return redirect('staff_leaves')