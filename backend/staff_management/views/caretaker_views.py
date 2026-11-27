from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from accounts.dashboard import record_audit_log
from children.models import Child, HealthRecord
from meals.models import ChildAllergy, MealRecord, MealSchedule
from sponsorships.models import Notification, SponsorshipMessage
from ..forms import CaretakerDailyCareForm, CaretakerIncidentForm, CaretakerMealLogForm
from ..models import CareIncident, DailyCareLog
from ..access import get_active_staff_member, is_caretaker


def caretaker_shell_context(request, staff_member, active_section):
    caretaker_name = request.user.get_full_name() or request.user.username or 'Care Taker'
    initials = ''.join(part[0] for part in caretaker_name.split()[:2]).upper() or 'CT'
    page_titles = {
        'caretaker_dashboard': 'My Dashboard',
        'caretaker_children': 'My Children',
        'caretaker_meal_log': 'Daily Meal Log',
        'caretaker_daily_care': 'Daily Care Log',
        'caretaker_incident_report': 'Report an Incident',
        'caretaker_incidents': 'Incident Reports',
        'caretaker_education_tracking': 'Education Tracking',
        'caretaker_health_tracking': 'Health Tracking',
        'caretaker_messages': 'Child Messages',
    }
    page_title = page_titles[active_section]

    return {
        'staff_member': staff_member,
        'nav_items': [
            {
                'id': 'caretaker_dashboard',
                'label': 'My Dashboard',
                'icon': 'bi bi-speedometer2',
                'url': reverse('caretaker_dashboard'),
            },
            {
                'id': 'caretaker_children',
                'label': 'My Children',
                'icon': 'bi bi-people',
                'url': reverse('caretaker_children'),
            },
            {
                'id': 'caretaker_incidents',
                'label': 'Incident Reports',
                'icon': 'bi bi-exclamation-triangle',
                'url': reverse('caretaker_incidents'),
            },
            {
                'id': 'caretaker_education_tracking',
                'label': 'Education Tracking',
                'icon': 'bi bi-journal-check',
                'url': reverse('caretaker_education_tracking'),
            },
            {
                'id': 'caretaker_health_tracking',
                'label': 'Health Tracking',
                'icon': 'bi bi-heart-pulse',
                'url': reverse('caretaker_health_tracking'),
            },
            {
                'id': 'caretaker_messages',
                'label': 'Child Messages',
                'icon': 'bi bi-chat-dots',
                'url': reverse('caretaker_messages'),
            },
        ],
        'active_section': active_section,
        'page_title': page_title,
        'active_nav_item': {'label': page_title},
        'active_management_section': None,
        'admin_name': caretaker_name,
        'admin_role': 'Care Taker',
        'user_initials': initials[:2],
    }


def _get_caretaker(request):
    staff_member = get_active_staff_member(request.user)
    if not is_caretaker(staff_member):
        messages.error(request, 'Only active care taker accounts can access this page.')
        return None
    return staff_member


@login_required(login_url='/accounts/admin_login/?role=staff')
def caretaker_dashboard(request):
    staff_member = _get_caretaker(request)
    if staff_member is None:
        return redirect('index')

    today = timezone.localdate()
    assigned_children = Child.objects.filter(caretakers=staff_member)
    todays_records = MealRecord.objects.filter(
        child__caretakers=staff_member,
        date=today,
    )
    assigned_incidents = CareIncident.objects.filter(child__caretakers=staff_member)
    children = assigned_children.annotate(
        today_meal_count=Count(
            'meal_records',
            filter=Q(meal_records__date=today),
        ),
    ).order_by('full_name')

    context = caretaker_shell_context(request, staff_member, 'caretaker_dashboard')
    context.update({
        'children': children,
        'child_count': assigned_children.distinct().count(),
        'meal_record_count': todays_records.count(),
        'refused_meal_count': todays_records.filter(status='refused').count(),
        'absent_meal_count': todays_records.filter(status='absent').count(),
        'daily_care_count': DailyCareLog.objects.filter(
            child__caretakers=staff_member,
            date=today,
        ).count(),
        'open_incident_count': assigned_incidents.filter(status='open').count(),
        'recent_incidents': assigned_incidents.select_related(
            'child',
            'reported_by',
        )[:5],
    })
    return render(request, 'staff_management/caretaker_dashboard.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def caretaker_children(request):
    staff_member = _get_caretaker(request)
    if staff_member is None:
        return redirect('index')

    today = timezone.localdate()
    children = Child.objects.filter(caretakers=staff_member).annotate(
        today_meal_count=Count(
            'meal_records',
            filter=Q(meal_records__date=today),
        ),
    ).order_by('full_name')
    allergies_by_child = {
        allergy.child_id: allergy
        for allergy in ChildAllergy.objects.filter(child__caretakers=staff_member)
    }
    child_rows = [
        {
            'child': child,
            'allergy': allergies_by_child.get(child.pk),
            'today_meal_count': child.today_meal_count,
            'daily_care_log_url': reverse('caretaker_daily_care', args=[child.pk]),
            'incident_report_url': reverse('caretaker_incident_report', args=[child.pk]),
        }
        for child in children
    ]

    context = caretaker_shell_context(request, staff_member, 'caretaker_children')
    context.update({
        'child_rows': child_rows,
        'child_count': len(child_rows),
    })
    return render(request, 'staff_management/caretaker_children.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def caretaker_education_tracking(request):
    staff_member = _get_caretaker(request)
    if staff_member is None:
        return redirect('index')

    today = timezone.localdate()
    period_start = today - timedelta(days=29)
    children = Child.objects.filter(caretakers=staff_member).select_related(
        'education_record',
        'education_record__class_teacher__user',
    ).annotate(
        attendance_days=Count(
            'attendances',
            filter=Q(attendances__date__gte=period_start, attendances__date__lte=today),
        ),
        present_days=Count(
            'attendances',
            filter=Q(
                attendances__date__gte=period_start,
                attendances__date__lte=today,
                attendances__status__in=('present', 'late'),
            ),
        ),
        absent_days=Count(
            'attendances',
            filter=Q(
                attendances__date__gte=period_start,
                attendances__date__lte=today,
                attendances__status='absent',
            ),
        ),
    ).order_by('full_name')
    child_rows = []
    for child in children:
        attendance_rate = (
            round(child.present_days * 100 / child.attendance_days, 1)
            if child.attendance_days else None
        )
        child_rows.append({
            'child': child,
            'education_record': getattr(child, 'education_record', None),
            'attendance_days': child.attendance_days,
            'present_days': child.present_days,
            'absent_days': child.absent_days,
            'attendance_rate': attendance_rate,
        })

    context = caretaker_shell_context(request, staff_member, 'caretaker_education_tracking')
    context.update({
        'child_rows': child_rows,
        'period_start': period_start,
        'today': today,
    })
    return render(request, 'staff_management/caretaker_education_tracking.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def caretaker_health_tracking(request):
    staff_member = _get_caretaker(request)
    if staff_member is None:
        return redirect('index')

    children = list(
        Child.objects.filter(caretakers=staff_member).order_by('full_name')
    )
    latest_record_by_child = {}
    for record in HealthRecord.objects.filter(
        child__caretakers=staff_member,
    ).select_related('child').order_by('child_id', '-last_checkup', '-pk'):
        latest_record_by_child.setdefault(record.child_id, record)
    allergy_by_child = {
        allergy.child_id: allergy
        for allergy in ChildAllergy.objects.filter(child__caretakers=staff_member)
    }
    child_rows = [
        {
            'child': child,
            'latest_record': latest_record_by_child.get(child.pk),
            'allergy': allergy_by_child.get(child.pk),
        }
        for child in children
    ]

    context = caretaker_shell_context(request, staff_member, 'caretaker_health_tracking')
    context.update({'child_rows': child_rows})
    return render(request, 'staff_management/caretaker_health_tracking.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def caretaker_messages(request):
    staff_member = _get_caretaker(request)
    if staff_member is None:
        return redirect('index')

    message_queryset = SponsorshipMessage.objects.filter(
        conversation__sponsorship__status='active',
        conversation__sponsorship__child__caretakers=staff_member,
        conversation__staff=staff_member,
    ).select_related(
        'sender',
        'conversation__sponsorship__child',
        'conversation__sponsorship__sponsor',
        'conversation__staff__user',
    ).order_by('-created_at')
    Notification.objects.filter(
        recipient=request.user,
        title='New message about an assigned child',
        url=reverse('caretaker_messages'),
        read_at__isnull=True,
    ).update(read_at=timezone.now())

    context = caretaker_shell_context(request, staff_member, 'caretaker_messages')
    context.update({
        'conversation_messages': message_queryset,
        'message_count': message_queryset.count(),
    })
    return render(request, 'staff_management/caretaker_messages.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def caretaker_daily_care(request, pk):
    staff_member = _get_caretaker(request)
    if staff_member is None:
        return redirect('index')

    child = get_object_or_404(Child.objects.filter(caretakers=staff_member), pk=pk)
    today = timezone.localdate()
    submitted_date = request.POST.get('date') if request.method == 'POST' else request.GET.get('date')
    selected_date = parse_date(submitted_date) if submitted_date else today
    if selected_date is None or (request.method == 'GET' and selected_date > today):
        messages.error(request, 'Choose a valid care-log date that is not in the future.')
        selected_date = today

    care_log = DailyCareLog.objects.filter(
        child=child,
        date=selected_date,
        shift=staff_member.shift,
    ).first()
    form = CaretakerDailyCareForm(
        request.POST if request.method == 'POST' else None,
        instance=care_log,
        initial={'date': selected_date},
    )
    if request.method == 'POST' and form.is_valid():
        care_log = form.save(commit=False)
        is_new = care_log.pk is None
        care_log.child = child
        care_log.caretaker = staff_member
        care_log.shift = staff_member.shift
        care_log.save()
        record_audit_log(
            request,
            'CREATE' if is_new else 'UPDATE',
            'Daily Care',
            record_id=str(care_log.pk),
            details=f'Recorded care notes for: {child.full_name}',
        )
        messages.success(request, 'Daily care log saved.')
        return redirect(
            f"{reverse('caretaker_daily_care', args=[child.pk])}?date="
            f"{form.cleaned_data['date'].isoformat()}"
        )

    context = caretaker_shell_context(request, staff_member, 'caretaker_daily_care')
    context.update({
        'child': child,
        'form': form,
        'selected_date': selected_date,
        'today': today,
    })
    return render(request, 'staff_management/caretaker_daily_care.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def caretaker_incident_report(request, pk):
    staff_member = _get_caretaker(request)
    if staff_member is None:
        return redirect('index')

    child = get_object_or_404(Child.objects.filter(caretakers=staff_member), pk=pk)
    if request.method == 'POST':
        form = CaretakerIncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.child = child
            incident.reported_by = staff_member
            incident.save()
            record_audit_log(
                request,
                'CREATE',
                'Care Incidents',
                record_id=str(incident.pk),
                details=f'Reported a care incident for: {child.full_name}',
            )
            messages.success(request, 'Incident report saved for review.')
            return redirect('caretaker_incidents')
    else:
        form = CaretakerIncidentForm()

    context = caretaker_shell_context(request, staff_member, 'caretaker_incident_report')
    context.update({'form': form, 'child': child})
    return render(request, 'staff_management/caretaker_incident_form.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def caretaker_incidents(request):
    staff_member = _get_caretaker(request)
    if staff_member is None:
        return redirect('index')

    incidents = CareIncident.objects.filter(
        child__caretakers=staff_member,
    ).select_related('child', 'reported_by', 'reviewed_by')
    context = caretaker_shell_context(request, staff_member, 'caretaker_incidents')
    context.update({'incidents': incidents})
    return render(request, 'staff_management/caretaker_incidents.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def caretaker_meal_log(request, pk):
    staff_member = _get_caretaker(request)
    if staff_member is None:
        return redirect('index')

    child = get_object_or_404(Child.objects.filter(caretakers=staff_member), pk=pk)
    today = timezone.localdate()
    submitted_date = request.POST.get('date') if request.method == 'POST' else request.GET.get('date')
    selected_date = parse_date(submitted_date) if submitted_date else today
    if selected_date is None or (request.method == 'GET' and selected_date > today):
        messages.error(request, 'Choose a valid meal-log date that is not in the future.')
        selected_date = today

    schedules = list(
        MealSchedule.objects.filter(
            day=selected_date.strftime('%A').lower(),
            is_active=True,
        ).order_by('meal_type')
    )
    records_by_type = {
        record.meal_type: record
        for record in MealRecord.objects.filter(child=child, date=selected_date)
    }
    form = CaretakerMealLogForm(
        request.POST if request.method == 'POST' else None,
        schedules=schedules,
        records_by_type=records_by_type,
        initial={'date': selected_date},
    )
    meal_rows = [
        {
            'schedule': schedule,
            'status_field': form[f'status_{schedule.meal_type}'],
            'notes_field': form[f'notes_{schedule.meal_type}'],
        }
        for schedule in schedules
    ]

    if request.method == 'POST':
        if not schedules:
            messages.error(request, 'There is no active meal schedule for this date.')
            return redirect('caretaker_meal_log', pk=child.pk)
        if form.is_valid():
            with transaction.atomic():
                for schedule in schedules:
                    MealRecord.objects.update_or_create(
                        child=child,
                        date=form.cleaned_data['date'],
                        meal_type=schedule.meal_type,
                        defaults={
                            'scheduled_food': schedule.food_items,
                            'status': form.cleaned_data[f'status_{schedule.meal_type}'],
                            'activity_notes': form.cleaned_data[f'notes_{schedule.meal_type}'],
                            'recorded_by': staff_member,
                        },
                    )
            messages.success(request, f'Meal log saved for {child.full_name}.')
            return redirect(
                f"{reverse('caretaker_meal_log', args=[child.pk])}?date="
                f"{form.cleaned_data['date'].isoformat()}"
            )

    allergy = ChildAllergy.objects.filter(child=child).first()
    context = caretaker_shell_context(request, staff_member, 'caretaker_meal_log')
    context.update({
        'form': form,
        'child': child,
        'allergy': allergy,
        'schedules': schedules,
        'meal_rows': meal_rows,
        'selected_date': selected_date,
        'today': today,
    })
    return render(request, 'staff_management/caretaker_meal_log.html', context)
