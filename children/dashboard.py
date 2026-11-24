from django.urls import reverse
from django.utils import timezone

from core.dashboard import badge, initials

from .models import Child, EducationRecord, HealthRecord


HEALTH_BADGES = {
    'healthy': 'success',
    'under_care': 'warning',
    'medical_care': 'danger',
    'observation': 'warning',
}


def children_section():
    rows = []
    for child in Child.objects.all().prefetch_related('sponsorships')[:50]:
        sponsorship = child.sponsorships.filter(status='active').first()
        photo_cell = ''
        if child.photo:
            photo_cell = (
                '<div class="avatar-sm overflow-hidden rounded-circle" style="width:38px;height:38px;">'
                f'<img src="{child.photo.url}" alt="{child.full_name}" '
                'style="width:100%;height:100%;object-fit:cover;">'
                '</div>'
            )
        else:
            photo_cell = f'<div class="avatar-sm bg-primary text-white">{initials(child.full_name)}</div>'

        rows.append({
            'view_url': reverse('child_detail', args=[child.pk]),
            'edit_url': reverse('child_update', args=[child.pk]),
            'delete_url': reverse('child_delete', args=[child.pk]),
            'delete_label': child.full_name,
            'cells': [
                child.child_id,
                photo_cell,
                child.full_name,
                child.age,
                child.date_of_birth or '',
                child.get_gender_display() if child.gender else '',
                badge(child.get_health_status_display(), HEALTH_BADGES.get(child.health_status, 'success')),
                child.education_level,
                badge(child.get_sponsor_status_display(), 'success' if child.sponsor_status == 'sponsored' else 'warning'),
                sponsorship.sponsor_name if sponsorship else 'Unassigned',
                child.admission_date,
                child.emergency_contact,
            ],
        })

    return {
        'id': 'children',
        'title': 'Children Management',
        'icon': 'bi bi-people-fill',
        'action_label': 'Add Child',
        'action_url': reverse('child_create'),
        'empty_message': 'No children records found. Add a child from the Children module.',
        'headings': ['ID', 'Photo', 'Full Name', 'Age', 'DOB', 'Gender', 'Health Status', 'Education Level', 'Sponsor Status', 'Sponsor Name', 'Admission Date', 'Emergency Contact'],
        'rows': rows,
    }


def health_section():
    rows = []
    today = timezone.localdate()
    
    children_with_records = Child.objects.filter(
        health_records__isnull=False
    ).distinct().prefetch_related('health_records')[:50]
    
    for child in children_with_records:
        records = list(child.health_records.all())
        
        if not records:
            continue
        
        latest_record = max(records, key=lambda r: r.last_checkup)
        
        pending_followups = sum(
            1 for r in records
            if r.follow_up_status == 'pending' and r.follow_up_due
        )
        overdue_followups = sum(
            1 for r in records
            if r.follow_up_status == 'pending' and r.follow_up_due and r.follow_up_due < today
        )
        
        next_followup_dates = [
            r.follow_up_due for r in records
            if r.follow_up_status == 'pending' and r.follow_up_due and r.follow_up_due >= today
        ]
        next_followup = min(next_followup_dates) if next_followup_dates else None
        
        status_badge = badge(child.get_health_status_display(), HEALTH_BADGES.get(child.health_status, 'success'))
        
        record_type_colors = {
            'checkup': 'info',
            'vaccination': 'success',
            'illness': 'warning',
            'emergency': 'danger',
            'followup': 'secondary',
            'lab': 'primary',
        }
        latest_type_badge = badge(latest_record.get_record_type_display(), record_type_colors.get(latest_record.record_type, 'info'))
        
        followup_status = ''
        if overdue_followups > 0:
            followup_status = f'<span class="badge bg-danger"><i class="bi bi-exclamation-triangle me-1"></i>{overdue_followups} Overdue</span>'
        elif pending_followups > 0:
            followup_status = f'<span class="badge bg-warning text-dark">{pending_followups} Pending</span>'
        else:
            followup_status = '<span class="badge bg-success">All Clear</span>'
        
        rows.append({
            'view_url': reverse('child_health_timeline', args=[child.pk]),
            'edit_url': reverse('health_record_update', args=[latest_record.pk]),
            'delete_url': reverse('health_record_delete', args=[latest_record.pk]),
            'delete_label': f'{child.full_name} - {latest_record.get_record_type_display()} on {latest_record.last_checkup}',
            'cells': [
                child.child_id,
                child.full_name,
                child.age,
                f'<span title="{latest_record.last_checkup}">{latest_record.last_checkup.strftime("%b %d, %Y")}</span>',
                latest_type_badge,
                latest_record.doctor_name or '-',
                f'<span class="badge bg-primary">{len(records)}</span>',
                f'<span class="badge bg-secondary">{pending_followups}</span>',
                next_followup.strftime('%b %d') if next_followup else '-',
                status_badge,
                followup_status,
            ],
        })

    return {
        'id': 'health',
        'title': 'Health & Medical Records',
        'icon': 'bi bi-heart-pulse',
        'action_label': 'Add Health Record',
        'action_url': reverse('health_record_create'),
        'empty_message': 'No health records found. Add a health record from the Health module.',
        'headings': ['Child ID', 'Name', 'Age', 'Latest Checkup', 'Type', 'Doctor', 'Total Records', 'Pending Follow-ups', 'Next Follow-up', 'Health Status', 'Follow-up Status'],
        'rows': rows,
    }


def education_section():
    rows = []
    for record in EducationRecord.objects.select_related('child', 'class_teacher__user')[:50]:
        attendance_kind = 'danger' if record.attendance_percent < 75 else 'success'
        
        # Get teacher name
        teacher_name = '-'
        if record.class_teacher:
            if record.class_teacher.user:
                teacher_name = record.class_teacher.user.get_full_name() or record.class_teacher.user.username
            else:
                teacher_name = record.class_teacher.staff_id
        
        rows.append({
            'view_url': reverse('education_record_detail', args=[record.pk]),
            'edit_url': reverse('education_record_update', args=[record.pk]),
            'delete_url': reverse('education_record_delete', args=[record.pk]),
            'delete_label': f'{record.child.full_name} education record',
            'cells': [
                f'<strong>{record.child.full_name}</strong><br><span class="text-muted small">{record.child.child_id}</span>',
                record.get_grade_level_display() or '-',
                record.roll_number or '-',
                teacher_name,
                badge(f'{record.attendance_percent:.1f}%', attendance_kind),
                record.academic_year or '-',
            ],
        })

    return {
        'id': 'education',
        'title': 'Education Tracking',
        'icon': 'bi bi-book',
        'action_label': 'Add Education Record',
        'action_url': reverse('education_record_create'),
        'empty_message': 'No education records found.',
        'headings': ['Child', 'Grade Level', 'Roll Number', 'Class Teacher', 'Attendance', 'Academic Year', 'Actions'],
        'rows': rows,
    }


def stats():
    total = Child.objects.count()
    sponsored = Child.objects.filter(sponsor_status='sponsored').count()
    health_alerts = Child.objects.exclude(health_status='healthy').count()
    return {
        'total_children': total,
        'sponsored_children': sponsored,
        'health_alerts': health_alerts,
    }