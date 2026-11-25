import logging
import re

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from accounts.views import is_admin_user, resolve_redirect
from accounts.dashboard import record_audit_log
from ..models import Child, HealthRecord
from ..forms import HealthRecordForm

logger = logging.getLogger(__name__)


def _weight_in_kg(value):
    match = re.fullmatch(r'\s*(\d+(?:[.,]\d+)?)\s*(?:kg|kgs|kilograms?)?\s*', value, re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1).replace(',', '.'))


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


@login_required(login_url='admin_login')
@require_POST
def analyze_child_health_patterns(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    child = get_object_or_404(Child, pk=pk)
    records = list(child.health_records.order_by('last_checkup', 'pk'))
    if not records:
        messages.error(request, 'Add a health record before analyzing patterns.')
        return redirect('child_health_timeline', pk=child.pk)

    payload_records = []
    skipped_weights = 0
    for record in records:
        weight_kg = _weight_in_kg(record.weight) if record.weight else None
        if record.weight and weight_kg is None:
            skipped_weights += 1
        payload_records.append({
            'date': record.last_checkup.isoformat(),
            'weight_kg': weight_kg,
            'temperature_c': float(record.temperature_c) if record.temperature_c is not None else None,
            'symptoms': [
                symptom.strip()
                for symptom in re.split(r'[,;\n]+', record.symptoms)
                if symptom.strip()
            ],
        })

    headers = {}
    if settings.AI_SERVICE_API_KEY:
        headers['X-API-Key'] = settings.AI_SERVICE_API_KEY

    try:
        response = requests.post(
            f'{settings.AI_SERVICE_URL.rstrip("/")}/health-pattern',
            json={'child_id': child.child_id, 'records': payload_records},
            headers=headers,
            timeout=(3, 10),
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or not isinstance(result.get('alerts'), list):
            raise ValueError('The AI service returned an invalid response.')
    except ValueError:
        logger.exception('AI health-pattern response was invalid for child %s', child.pk)
        messages.error(request, 'The AI service returned an invalid response. Please try again later.')
        return redirect('child_health_timeline', pk=child.pk)
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 'unknown'
        logger.exception('AI health-pattern request returned HTTP %s for child %s', status_code, child.pk)
        messages.error(
            request,
            f'The AI service returned HTTP {status_code}. Check the shared API key and health data.',
        )
        return redirect('child_health_timeline', pk=child.pk)
    except requests.RequestException:
        logger.exception('AI health-pattern request failed for child %s', child.pk)
        messages.error(request, 'Could not reach the AI service. Check that it is running, then try again.')
        return redirect('child_health_timeline', pk=child.pk)

    session_key = f'health_pattern_result_{child.pk}'
    request.session[session_key] = result
    request.session[f'health_pattern_warnings_{child.pk}'] = (
        ['Some weight values were skipped because they were not entered as kilograms.']
        if skipped_weights else []
    )
    record_audit_log(
        request, 'ANALYZE', 'Health Patterns',
        record_id=child.child_id,
        details=f'Analyzed health patterns for: {child.full_name}'
    )
    return redirect('child_health_timeline', pk=child.pk)