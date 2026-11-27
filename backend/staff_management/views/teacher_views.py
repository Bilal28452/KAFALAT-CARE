from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from children.models import Attendance, EducationRecord, EducationResult
from ..access import get_active_staff_member, is_teacher
from ..forms import TeacherAttendanceForm, TeacherEducationResultForm


def teacher_shell_context(request, staff_member, active_section):
    teacher_name = request.user.get_full_name() or request.user.username or 'Teacher'
    initials = ''.join(part[0] for part in teacher_name.split()[:2]).upper() or 'TC'
    page_titles = {
        'teacher_dashboard': 'My Dashboard',
        'teacher_students': 'My Students',
        'teacher_attendance': 'Attendance',
        'teacher_results': 'Results',
    }
    page_title = page_titles[active_section]

    return {
        'staff_member': staff_member,
        'nav_items': [
            {
                'id': 'teacher_dashboard',
                'label': 'My Dashboard',
                'icon': 'bi bi-speedometer2',
                'url': reverse('teacher_dashboard'),
            },
            {
                'id': 'teacher_students',
                'label': 'My Students',
                'icon': 'bi bi-people',
                'url': reverse('teacher_students'),
            },
            {
                'id': 'teacher_attendance',
                'label': 'Attendance',
                'icon': 'bi bi-calendar-check',
                'url': reverse('teacher_attendance'),
            },
            {
                'id': 'teacher_results',
                'label': 'Results',
                'icon': 'bi bi-award',
                'url': reverse('teacher_results'),
            },
        ],
        'active_section': active_section,
        'page_title': page_title,
        'active_nav_item': {'label': page_title},
        'active_management_section': None,
        'admin_name': teacher_name,
        'admin_role': 'Teacher',
        'user_initials': initials[:2],
    }


@login_required(login_url='/accounts/admin_login/?role=staff')
def teacher_dashboard(request):
    staff_member = get_active_staff_member(request.user)
    if not is_teacher(staff_member):
        messages.error(request, 'Only active teacher accounts can access this dashboard.')
        return redirect('index')

    assigned_records = EducationRecord.objects.filter(class_teacher=staff_member)
    assigned_child_ids = assigned_records.values('child_id')
    teacher_results = EducationResult.objects.filter(
        teacher=staff_member,
        child_id__in=assigned_child_ids,
    ).select_related('child', 'course')

    context = teacher_shell_context(request, staff_member, 'teacher_dashboard')
    context.update({
        'student_count': assigned_records.count(),
        'class_count': assigned_records.exclude(grade_level='').values('grade_level').distinct().count(),
        'result_count': teacher_results.count(),
        'average_score': teacher_results.aggregate(average=Avg('score'))['average'] or 0,
        'recent_results': teacher_results.order_by('-created_at')[:5],
    })
    return render(request, 'staff_management/teacher_dashboard.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def teacher_students(request):
    staff_member = get_active_staff_member(request.user)
    if not is_teacher(staff_member):
        messages.error(request, 'Only active teacher accounts can access this page.')
        return redirect('index')

    education_records = EducationRecord.objects.filter(
        class_teacher=staff_member,
    ).select_related('child').order_by('child__full_name')

    context = teacher_shell_context(request, staff_member, 'teacher_students')
    context.update({
        'education_records': education_records,
        'student_count': education_records.count(),
    })
    return render(request, 'staff_management/teacher_students.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def teacher_attendance(request):
    staff_member = get_active_staff_member(request.user)
    if not is_teacher(staff_member):
        messages.error(request, 'Only active teacher accounts can access attendance.')
        return redirect('index')

    education_records = list(
        EducationRecord.objects.filter(class_teacher=staff_member)
        .select_related('child')
        .order_by('child__full_name')
    )
    today = timezone.localdate()
    submitted_date = request.POST.get('date') if request.method == 'POST' else request.GET.get('date')
    selected_date = parse_date(submitted_date) if submitted_date else today
    if selected_date is None or (request.method == 'GET' and selected_date > today):
        messages.error(request, 'Choose a valid attendance date that is not in the future.')
        selected_date = today


    attendance_by_child = {
        attendance.child_id: attendance
        for attendance in Attendance.objects.filter(
            child_id__in=[record.child_id for record in education_records],
            date=selected_date,
        )
    }
    form = TeacherAttendanceForm(
        request.POST if request.method == 'POST' else None,
        education_records=education_records,
        attendance_by_child=attendance_by_child,
        initial={'date': selected_date},
    )

    if request.method == 'POST':
        if not education_records:
            messages.error(request, 'There are no students assigned to your account.')
            return redirect('teacher_attendance')
        if form.is_valid():
            marked_by = request.user.get_full_name() or staff_member.staff_id
            with transaction.atomic():
                for record in education_records:
                    Attendance.objects.update_or_create(
                        child=record.child,
                        date=form.cleaned_data['date'],
                        defaults={
                            'status': form.cleaned_data[f'status_{record.child_id}'],
                            'marked_by': marked_by,
                        },
                    )

            attendance_date = form.cleaned_data['date']
            messages.success(request, 'Attendance saved successfully.')
            return redirect(f"{reverse('teacher_attendance')}?date={attendance_date.isoformat()}")

    students = [
        {
            'record': record,
            'status_field': form[f'status_{record.child_id}'],
        }
        for record in education_records
    ]
    context = teacher_shell_context(request, staff_member, 'teacher_attendance')
    context.update({
        'attendance_form': form,
        'attendance_by_child': attendance_by_child,
        'selected_date': selected_date,
        'today': today,
        'students': students,
        'student_count': len(education_records),
        'present_count': sum(item.status == 'present' for item in attendance_by_child.values()),
        'absent_count': sum(item.status == 'absent' for item in attendance_by_child.values()),
        'late_count': sum(item.status == 'late' for item in attendance_by_child.values()),
        'leave_count': sum(item.status == 'leave' for item in attendance_by_child.values()),
    })
    return render(request, 'staff_management/teacher_attendance.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def teacher_results(request):
    staff_member = get_active_staff_member(request.user)
    if not is_teacher(staff_member):
        messages.error(request, 'Only active teacher accounts can access results.')
        return redirect('index')

    results = EducationResult.objects.filter(
        teacher=staff_member,
        child__education_record__class_teacher=staff_member,
    ).select_related('child', 'course').order_by('-created_at')
    context = teacher_shell_context(request, staff_member, 'teacher_results')
    context.update({
        'results': results,
        'result_count': results.count(),
    })
    return render(request, 'staff_management/teacher_results.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def teacher_result_create(request):
    staff_member = get_active_staff_member(request.user)
    if not is_teacher(staff_member):
        messages.error(request, 'Only active teacher accounts can record results.')
        return redirect('index')

    if request.method == 'POST':
        form = TeacherEducationResultForm(request.POST, staff_member=staff_member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Result recorded successfully.')
            return redirect('teacher_results')
    else:
        form = TeacherEducationResultForm(staff_member=staff_member)

    context = teacher_shell_context(request, staff_member, 'teacher_results')
    context.update({'form': form, 'action': 'Add'})
    return render(request, 'staff_management/teacher_result_form.html', context)


@login_required(login_url='/accounts/admin_login/?role=staff')
def teacher_result_update(request, pk):
    staff_member = get_active_staff_member(request.user)
    if not is_teacher(staff_member):
        messages.error(request, 'Only active teacher accounts can update results.')
        return redirect('index')

    result = get_object_or_404(
        EducationResult.objects.select_related('child', 'course'),
        pk=pk,
        teacher=staff_member,
        child__education_record__class_teacher=staff_member,
    )
    if request.method == 'POST':
        form = TeacherEducationResultForm(request.POST, instance=result, staff_member=staff_member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Result updated successfully.')
            return redirect('teacher_results')
    else:
        form = TeacherEducationResultForm(instance=result, staff_member=staff_member)

    context = teacher_shell_context(request, staff_member, 'teacher_results')
    context.update({'form': form, 'action': 'Update', 'result': result})
    return render(request, 'staff_management/teacher_result_form.html', context)
