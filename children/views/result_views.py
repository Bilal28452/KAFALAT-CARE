from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from accounts.views import is_admin_user
from accounts.dashboard import record_audit_log
from ..models import EducationResult
from ..forms import EducationResultForm


@login_required(login_url='admin_login')
def education_result_list(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    results = EducationResult.objects.select_related('child', 'course', 'teacher').all()
    search_query = request.GET.get('search', '')
    if search_query:
        results = results.filter(
            Q(child__full_name__icontains=search_query) |
            Q(course__title__icontains=search_query)
        )

    record_audit_log(request, 'VIEW', 'Education Results', details='Viewed education results list')
    return render(request, 'children/education_result_list.html', {'results': results, 'search_query': search_query})


@login_required(login_url='admin_login')
def education_result_create(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    if request.method == 'POST':
        form = EducationResultForm(request.POST)
        if form.is_valid():
            result = form.save()
            record_audit_log(request, 'CREATE', 'Education Results', record_id=str(result.pk), details=f'Created result for {result.child.full_name}')
            messages.success(request, 'Result recorded successfully.')
            return redirect('education_result_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = EducationResultForm()

    return render(request, 'children/education_result_form.html', {'form': form, 'action': 'Create'})


@login_required(login_url='admin_login')
def education_result_detail(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    result = get_object_or_404(EducationResult.objects.select_related('child', 'course', 'teacher'), pk=pk)
    record_audit_log(request, 'VIEW', 'Education Results', record_id=str(result.pk), details=f'Viewed result for {result.child.full_name}')
    return render(request, 'children/education_result_detail.html', {'result': result})


@login_required(login_url='admin_login')
def education_result_update(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    result = get_object_or_404(EducationResult, pk=pk)
    if request.method == 'POST':
        form = EducationResultForm(request.POST, instance=result)
        if form.is_valid():
            result = form.save()
            record_audit_log(request, 'UPDATE', 'Education Results', record_id=str(result.pk), details=f'Updated result for {result.child.full_name}')
            messages.success(request, 'Result updated successfully.')
            return redirect('education_result_detail', pk=result.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = EducationResultForm(instance=result)

    return render(request, 'children/education_result_form.html', {'form': form, 'action': 'Update', 'result': result})


@login_required(login_url='admin_login')
def education_result_delete(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    result = get_object_or_404(EducationResult, pk=pk)
    if request.method == 'POST':
        result.delete()
        record_audit_log(request, 'DELETE', 'Education Results', record_id=str(pk), details=f'Deleted result for {result.child.full_name}')
        messages.success(request, 'Result deleted successfully.')
        return redirect('education_result_list')

    return render(request, 'children/education_result_confirm_delete.html', {'result': result})