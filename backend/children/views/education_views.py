from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q

from accounts.views import is_admin_user, resolve_redirect
from accounts.dashboard import record_audit_log
from ..models import EducationRecord, EducationResult
from ..forms import EducationRecordForm


@login_required(login_url='admin_login')
def education_record_list(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    education_records = EducationRecord.objects.select_related('child', 'class_teacher')
    
    search_query = request.GET.get('search', '')
    if search_query:
        education_records = education_records.filter(
            Q(child__child_id__icontains=search_query) |
            Q(child__full_name__icontains=search_query) |
            Q(roll_number__icontains=search_query)
        )

    grade_filter = request.GET.get('grade_level', '')
    if grade_filter:
        education_records = education_records.filter(grade_level=grade_filter)

    education_records = education_records.order_by('child__full_name')
    
    record_audit_log(request, 'VIEW', 'Education Records', details='Viewed education records list')
    
    grade_levels = EducationRecord.GRADE_LEVEL_CHOICES
    
    context = {
        'education_records': education_records,
        'search_query': search_query,
        'grade_levels': grade_levels,
        'grade_filter': grade_filter,
    }
    return render(request, 'children/education_record_list.html', context)


@login_required(login_url='admin_login')
def education_record_create(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    child_id = request.GET.get('child')
    if child_id:
        existing = EducationRecord.objects.filter(child_id=child_id).first()
        if existing:
            messages.warning(request, 'This child already has an education record. You can edit it instead.')
            return redirect('education_record_update', pk=existing.pk)
    
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if request.method == 'POST':
        form = EducationRecordForm(request.POST)
        if form.is_valid():
            education_record = form.save()
            record_audit_log(
                request, 'CREATE', 'Education Records',
                record_id=str(education_record.pk),
                details=f'Created education record for: {education_record.child.full_name}'
            )
            messages.success(request, f'Education record for {education_record.child.full_name} created successfully.')
            return redirect(resolve_redirect(request, reverse('education_record_detail', kwargs={'pk': education_record.pk})))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EducationRecordForm(initial={'child': request.GET.get('child')})
    
    context = {'form': form, 'action': 'Create', 'next': next_url}
    return render(request, 'children/education_record_form.html', context)


@login_required(login_url='admin_login')
def education_record_detail(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    education_record = get_object_or_404(EducationRecord.objects.select_related('child', 'class_teacher'), pk=pk)
    results = EducationResult.objects.filter(child=education_record.child).select_related('course', 'teacher')
    
    record_audit_log(
        request, 'VIEW', 'Education Records',
        record_id=str(education_record.pk),
        details=f'Viewed education record for: {education_record.child.full_name}'
    )
    
    context = {
        'education_record': education_record,
        'results': results,
    }
    return render(request, 'children/education_record_detail.html', context)


@login_required(login_url='admin_login')
def education_record_update(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    education_record = get_object_or_404(EducationRecord, pk=pk)
    next_url = request.POST.get('next') or request.GET.get('next', '')
    
    if request.method == 'POST':
        form = EducationRecordForm(request.POST, instance=education_record)
        if form.is_valid():
            education_record = form.save()
            record_audit_log(
                request, 'UPDATE', 'Education Records',
                record_id=str(education_record.pk),
                details=f'Updated education record for: {education_record.child.full_name}'
            )
            messages.success(request, f'Education record for {education_record.child.full_name} updated successfully.')
            return redirect(resolve_redirect(request, reverse('education_record_detail', kwargs={'pk': education_record.pk})))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EducationRecordForm(instance=education_record)
    
    context = {'form': form, 'action': 'Update', 'education_record': education_record, 'next': next_url}
    return render(request, 'children/education_record_form.html', context)


@login_required(login_url='admin_login')
def education_record_delete(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    education_record = get_object_or_404(EducationRecord, pk=pk)
    
    if request.method == 'POST':
        child_name = education_record.child.full_name
        record_id = str(education_record.pk)
        education_record.delete()
        record_audit_log(
            request, 'DELETE', 'Education Records',
            record_id=record_id,
            details=f'Deleted education record for: {child_name}'
        )
        messages.success(request, f'Education record for {child_name} deleted successfully.')
        return redirect(resolve_redirect(request, reverse('education_record_list')))
    
    context = {'education_record': education_record}
    return render(request, 'children/education_record_confirm_delete.html', context)