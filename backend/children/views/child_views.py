from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone

from accounts.views import is_admin_user
from accounts.dashboard import record_audit_log
from ..models import Child
from ..forms import ChildForm


@login_required(login_url='admin_login')
def child_list(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    children = Child.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        children = children.filter(
            Q(child_id__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(education_level__icontains=search_query)
        )
    
    sponsor_filter = request.GET.get('sponsor_status', '')
    if sponsor_filter:
        children = children.filter(sponsor_status=sponsor_filter)
    
    health_filter = request.GET.get('health_status', '')
    if health_filter:
        children = children.filter(health_status=health_filter)
    
    record_audit_log(request, 'VIEW', 'Children', details='Viewed children list')
    
    context = {
        'children': children,
        'search_query': search_query,
        'sponsor_filter': sponsor_filter,
        'health_filter': health_filter,
    }
    return render(request, 'children/child_list.html', context)


@login_required(login_url='admin_login')
def child_create(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        form = ChildForm(request.POST, request.FILES)
        if form.is_valid():
            child = form.save()
            record_audit_log(
                request, 'CREATE', 'Children',
                record_id=child.child_id,
                details=f'Created child record: {child.full_name}'
            )
            messages.success(request, f'Child record for {child.full_name} created successfully.')
            return redirect(reverse('dashboard') + '?section=children')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChildForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'children/child_form.html', context)


@login_required(login_url='admin_login')
def child_detail(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    child = get_object_or_404(Child, pk=pk)
    health_records = child.health_records.all()[:5]
    education_record = getattr(child, 'education_record', None)
    results = child.education_results.all()[:10]
    
    record_audit_log(
        request, 'VIEW', 'Children',
        record_id=child.child_id,
        details=f'Viewed child details: {child.full_name}'
    )
    
    context = {
        'child': child,
        'health_records': health_records,
        'education_record': education_record,
        'results': results,
    }
    return render(request, 'children/child_detail.html', context)


@login_required(login_url='admin_login')
def child_update(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    child = get_object_or_404(Child, pk=pk)
    
    if request.method == 'POST':
        form = ChildForm(request.POST, request.FILES, instance=child)
        if form.is_valid():
            child = form.save()
            record_audit_log(
                request, 'UPDATE', 'Children',
                record_id=child.child_id,
                details=f'Updated child record: {child.full_name}'
            )
            messages.success(request, f'Child record for {child.full_name} updated successfully.')
            return redirect(reverse('dashboard') + '?section=children')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChildForm(instance=child)
    
    context = {'form': form, 'action': 'Update', 'child': child}
    return render(request, 'children/child_form.html', context)


@login_required(login_url='admin_login')
def child_delete(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    child = get_object_or_404(Child, pk=pk)
    
    if request.method == 'POST':
        child_name = child.full_name
        child_id = child.child_id
        child.delete()
        record_audit_log(
            request, 'DELETE', 'Children',
            record_id=child_id,
            details=f'Deleted child record: {child_name}'
        )
        messages.success(request, f'Child record for {child_name} deleted successfully.')
        return redirect(reverse('dashboard') + '?section=children')
    
    context = {'child': child}
    return render(request, 'children/child_confirm_delete.html', context)


@login_required(login_url='admin_login')
def child_health_timeline(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    child = get_object_or_404(Child, pk=pk)
    health_records = child.health_records.order_by('last_checkup', 'pk')
    today = timezone.localdate()

    pending_followups = child.health_records.filter(follow_up_status='pending').count()
    overdue_followups = child.health_records.filter(
        follow_up_status='pending',
        follow_up_due__lt=today
    ).count()
    upcoming_followups = child.health_records.filter(
        follow_up_status='pending',
        follow_up_due__gte=today
    ).order_by('follow_up_due')[:5]

    record_audit_log(
        request, 'VIEW', 'Health Timeline',
        record_id=child.child_id,
        details=f'Viewed health timeline for: {child.full_name}'
    )

    context = {
        'child': child,
        'health_records': health_records,
        'pending_followups': pending_followups,
        'overdue_followups': overdue_followups,
        'upcoming_followups': upcoming_followups,
        'health_pattern_result': request.session.pop(f'health_pattern_result_{child.pk}', None),
        'health_pattern_warnings': request.session.pop(f'health_pattern_warnings_{child.pk}', []),
    }
    return render(request, 'children/child_health_timeline.html', context)