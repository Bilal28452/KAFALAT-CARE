from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.dashboard import record_audit_log
from children.forms import DoctorHealthRecordForm
from children.models import Child, HealthRecord
from ..access import get_active_staff_member, is_doctor
from ..forms import DoctorIncidentReviewForm
from ..models import CareIncident


def doctor_shell_context(request, staff_member, active_section):
    doctor_name = request.user.get_full_name() or request.user.username or 'Doctor'
    initials = ''.join(part[0] for part in doctor_name.split()[:2]).upper() or 'DR'
    page_titles = {
        'doctor_dashboard': 'My Dashboard',
        'doctor_patients': 'My Patients',
        'doctor_patient_detail': 'Patient Health Record',
        'doctor_incidents': 'Care Incidents',
        'doctor_incident_review': 'Review Care Incident',
    }
    page_title = page_titles[active_section]

    return {
        'staff_member': staff_member,
        'nav_items': [
            {
                'id': 'doctor_dashboard',
                'label': 'My Dashboard',
                'icon': 'bi bi-speedometer2',
                'url': reverse('doctor_dashboard'),
            },
            {
                'id': 'doctor_patients',
                'label': 'My Patients',
                'icon': 'bi bi-heart-pulse',
                'url': reverse('doctor_patients'),
            },
            {
                'id': 'doctor_incidents',
                'label': 'Care Incidents',
                'icon': 'bi bi-exclamation-triangle',
                'url': reverse('doctor_incidents'),
            },
        ],
        'active_section': active_section,
        'page_title': page_title,
        'active_nav_item': {'label': page_title},
        'active_management_section': None,
        'admin_name': doctor_name,
        'admin_role': 'Doctor',
        'user_initials': initials[:2],
    }


def _get_doctor(request):
    staff_member = get_active_staff_member(request.user)
    if not is_doctor(staff_member):
        messages.error(request, 'Only active doctor accounts can access this page.')
        return None
    return staff_member


@login_required(login_url='/accounts/admin_login/?role=staff')
def doctor_dashboard(request):
    staff_member = _get_doctor(request)
    if staff_member is None:
        return redirect('index')

    today = timezone.localdate()
    assigned_children = Child.objects.filter(doctors=staff_member)
    health_records = HealthRecord.objects.filter(child__doctors=staff_member)
    open_incidents = CareIncident.objects.filter(
        child__doctors=staff_member,
        status='open',
    ).select_related('child', 'reported_by')[:5]
    upcoming_followups = health_records.filter(
        follow_up_status='pending',
        follow_up_due__gte=today,
    ).select_related('child').order_by('follow_up_due', 'child__full_name')[:6]
    patients = assigned_children.annotate(
        health_record_count=Count('health_records'),
    ).order_by('full_name')

    context = doctor_shell_context(request, staff_member, 'doctor_dashboard')
    context.update({
        'patient_count': assigned_children.distinct().count(),
        'critical_record_count': health_records.filter(priority_level='critical').count(),
        'pending_followup_count': health_records.filter(
            follow_up_status='pending',
            follow_up_due__isnull=False,
        ).count(),
        'overdue_followup_count': health_records.filter(
            follow_up_status='pending',
            follow_up_due__lt=today,
        ).count(),
        'open_incident_count': CareIncident.objects.filter(
            child__doctors=staff_member,
            status='open',
        ).count(),
        'open_incidents': open_incidents,
        'upcoming_followups': upcoming_followups,
        'patients': patients,
    })
    return render(request, 'staff_management/doctor_dashboard.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def doctor_patients(request):
    staff_member = _get_doctor(request)
    if staff_member is None:
        return redirect('index')

    patients = Child.objects.filter(
        doctors=staff_member,
    ).annotate(
        health_record_count=Count('health_records'),
    ).order_by('full_name')

    context = doctor_shell_context(request, staff_member, 'doctor_patients')
    context.update({
        'patients': patients,
        'patient_count': patients.count(),
    })
    return render(request, 'staff_management/doctor_patients.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def doctor_patient_detail(request, pk):
    staff_member = _get_doctor(request)
    if staff_member is None:
        return redirect('index')

    patient = get_object_or_404(
        Child.objects.filter(doctors=staff_member),
        pk=pk,
    )
    health_records = patient.health_records.order_by('-last_checkup', '-pk')
    context = doctor_shell_context(request, staff_member, 'doctor_patient_detail')
    context.update({
        'patient': patient,
        'health_records': health_records,
    })
    return render(request, 'staff_management/doctor_patient_detail.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def doctor_incidents(request):
    staff_member = _get_doctor(request)
    if staff_member is None:
        return redirect('index')

    incidents = CareIncident.objects.filter(
        child__doctors=staff_member,
    ).select_related('child', 'reported_by', 'reviewed_by')
    context = doctor_shell_context(request, staff_member, 'doctor_incidents')
    context.update({
        'incidents': incidents,
        'open_incident_count': incidents.filter(status='open').count(),
    })
    return render(request, 'staff_management/doctor_incidents.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def doctor_incident_review(request, pk):
    staff_member = _get_doctor(request)
    if staff_member is None:
        return redirect('index')

    incident = get_object_or_404(
        CareIncident.objects.select_related('child').filter(child__doctors=staff_member),
        pk=pk,
    )
    if request.method == 'POST':
        form = DoctorIncidentReviewForm(request.POST, instance=incident)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.reviewed_by = staff_member
            incident.save()
            record_audit_log(
                request,
                'UPDATE',
                'Care Incidents',
                record_id=str(incident.pk),
                details=f'Reviewed a care incident for: {incident.child.full_name}',
            )
            messages.success(request, 'Incident review saved.')
            return redirect('doctor_incidents')
    else:
        form = DoctorIncidentReviewForm(instance=incident)

    context = doctor_shell_context(request, staff_member, 'doctor_incident_review')
    context.update({'form': form, 'incident': incident})
    return render(request, 'staff_management/doctor_incident_review.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def doctor_health_record_create(request, pk):
    staff_member = _get_doctor(request)
    if staff_member is None:
        return redirect('index')

    patient = get_object_or_404(Child.objects.filter(doctors=staff_member), pk=pk)
    if request.method == 'POST':
        form = DoctorHealthRecordForm(request.POST)
        if form.is_valid():
            health_record = form.save(commit=False)
            health_record.child = patient
            health_record.doctor_name = request.user.get_full_name() or staff_member.staff_id
            health_record.save()
            record_audit_log(
                request,
                'CREATE',
                'Health Records',
                record_id=str(health_record.pk),
                details=f'Doctor created a health record for: {patient.full_name}',
            )
            messages.success(request, 'Health record added successfully.')
            return redirect('doctor_patient_detail', pk=patient.pk)
    else:
        form = DoctorHealthRecordForm()

    context = doctor_shell_context(request, staff_member, 'doctor_patient_detail')
    context.update({
        'form': form,
        'patient': patient,
        'action': 'Add',
    })
    return render(request, 'staff_management/doctor_health_record_form.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def doctor_health_record_update(request, pk):
    staff_member = _get_doctor(request)
    if staff_member is None:
        return redirect('index')

    health_record = get_object_or_404(
        HealthRecord.objects.select_related('child').filter(child__doctors=staff_member),
        pk=pk,
    )
    if request.method == 'POST':
        form = DoctorHealthRecordForm(request.POST, instance=health_record)
        if form.is_valid():
            health_record = form.save()
            record_audit_log(
                request,
                'UPDATE',
                'Health Records',
                record_id=str(health_record.pk),
                details=f'Doctor updated a health record for: {health_record.child.full_name}',
            )
            messages.success(request, 'Health record updated successfully.')
            return redirect('doctor_patient_detail', pk=health_record.child_id)
    else:
        form = DoctorHealthRecordForm(instance=health_record)

    context = doctor_shell_context(request, staff_member, 'doctor_patient_detail')
    context.update({
        'form': form,
        'patient': health_record.child,
        'health_record': health_record,
        'action': 'Update',
    })
    return render(request, 'staff_management/doctor_health_record_form.html', context)
