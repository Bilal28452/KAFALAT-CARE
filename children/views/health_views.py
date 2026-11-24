from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from accounts.views import is_admin_user, resolve_redirect
from accounts.dashboard import record_audit_log
from ..models import HealthRecord
from ..forms import HealthRecordForm


@login_required(login_url='admin_login')
def health_record_create(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if request.method == 'POST':
        form = HealthRecordForm(request.POST)
        if form.is_valid():
            health_record = form.save()
            record_audit_log(
                request, 'CREATE', 'Health Records',
                record_id=str(health_record.pk),
                details=f'Created health record for: {health_record.child.full_name}'
            )
            messages.success(request, f'Health record for {health_record.child.full_name} created successfully.')
            return redirect(resolve_redirect(request, reverse('health_record_detail', kwargs={'pk': health_record.pk})))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HealthRecordForm(initial={'child': request.GET.get('child')})
    
    context = {'form': form, 'action': 'Create', 'next': next_url}
    return render(request, 'children/health_record_form.html', context)


@login_required(login_url='admin_login')
def health_record_detail(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    health_record = get_object_or_404(HealthRecord.objects.select_related('child'), pk=pk)
    
    record_audit_log(
        request, 'VIEW', 'Health Records',
        record_id=str(health_record.pk),
        details=f'Viewed health record for: {health_record.child.full_name}'
    )
    
    context = {'health_record': health_record}
    return render(request, 'children/health_record_detail.html', context)


@login_required(login_url='admin_login')
def health_record_update(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    health_record = get_object_or_404(HealthRecord, pk=pk)
    next_url = request.POST.get('next') or request.GET.get('next', '')
    
    if request.method == 'POST':
        form = HealthRecordForm(request.POST, instance=health_record)
        if form.is_valid():
            health_record = form.save()
            record_audit_log(
                request, 'UPDATE', 'Health Records',
                record_id=str(health_record.pk),
                details=f'Updated health record for: {health_record.child.full_name}'
            )
            messages.success(request, f'Health record for {health_record.child.full_name} updated successfully.')
            return redirect(resolve_redirect(request, reverse('health_record_detail', kwargs={'pk': health_record.pk})))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HealthRecordForm(instance=health_record)
    
    context = {'form': form, 'action': 'Update', 'health_record': health_record, 'next': next_url}
    return render(request, 'children/health_record_form.html', context)


@login_required(login_url='admin_login')
def health_record_delete(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    health_record = get_object_or_404(HealthRecord, pk=pk)
    
    if request.method == 'POST':
        child_name = health_record.child.full_name
        record_id = str(health_record.pk)
        health_record.delete()
        record_audit_log(
            request, 'DELETE', 'Health Records',
            record_id=record_id,
            details=f'Deleted health record for: {child_name}'
        )
        messages.success(request, f'Health record for {child_name} deleted successfully.')
        return redirect(resolve_redirect(request, reverse('dashboard') + '?section=health'))
    
    context = {'health_record': health_record}
    return render(request, 'children/health_record_confirm_delete.html', context)