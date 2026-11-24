from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q

from accounts.views import is_admin_user, resolve_redirect
from accounts.dashboard import record_audit_log
from ..models import StaffMember
from ..forms import StaffMemberForm


@login_required(login_url='admin_login')
def staff_list(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    staff_members = StaffMember.objects.select_related('user').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        staff_members = staff_members.filter(
            Q(staff_id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(position__icontains=search_query)
        )
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        staff_members = staff_members.filter(status=status_filter)
    
    context = {
        'staff_members': staff_members,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'staff_management/staff_list.html', context)


@login_required(login_url='admin_login')
def staff_create(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        form = StaffMemberForm(request.POST)
        if form.is_valid():
            staff_member = form.save()
            messages.success(request, f'Staff member added successfully.')
            return redirect('staff_detail', pk=staff_member.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffMemberForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'staff_management/staff_form.html', context)


@login_required(login_url='admin_login')
def staff_detail(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    staff_member = get_object_or_404(StaffMember.objects.select_related('user'), pk=pk)
    context = {'staff_member': staff_member}
    return render(request, 'staff_management/staff_detail.html', context)


@login_required(login_url='admin_login')
def staff_update(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    staff_member = get_object_or_404(StaffMember, pk=pk)
    
    if request.method == 'POST':
        form = StaffMemberForm(request.POST, instance=staff_member)
        if form.is_valid():
            form.save()
            messages.success(request, f'Staff member updated successfully.')
            return redirect('staff_detail', pk=staff_member.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffMemberForm(instance=staff_member)
    
    context = {'form': form, 'action': 'Update', 'staff_member': staff_member}
    return render(request, 'staff_management/staff_form.html', context)


@login_required(login_url='admin_login')
def staff_delete(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    staff_member = get_object_or_404(StaffMember, pk=pk)
    
    if request.method == 'POST':
        staff_member.delete()
        messages.success(request, f'Staff member deleted successfully.')
        return redirect(reverse('dashboard') + '?section=staff')
    
    context = {'staff_member': staff_member}
    return render(request, 'staff_management/staff_confirm_delete.html', context)