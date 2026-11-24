from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime

from accounts.views.auth_views import is_admin_user
from accounts.dashboard import record_audit_log
from ..models import StaffMember, StaffAttendance


@login_required(login_url='admin_login')
def staff_attendance(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    today = timezone.localdate()
    selected_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    status_filter = request.GET.get('attendance_status', '')
    
    try:
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except:
        date_obj = today
    
    # Get staff members with filters
    staff_members = StaffMember.objects.filter(employment_status='active')
    
    if search_query:
        staff_members = staff_members.filter(
            Q(staff_id__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    if department_filter:
        staff_members = staff_members.filter(department__icontains=department_filter)
    
    # Get existing attendance for this date
    attendance_dict = {}
    for att in StaffAttendance.objects.filter(date=date_obj):
        attendance_dict[att.staff_id] = att
    
    # Create staff_list with attendance data
    staff_list = []
    for staff in staff_members:
        att = attendance_dict.get(staff.id)
        staff_list.append({
            'staff': staff,
            'attendance': att,
            'status': att.status if att else '',
            'remarks': att.remarks if att else '',
        })
    
    # Apply attendance status filter after getting records
    if status_filter:
        if status_filter == 'not_marked':
            staff_list = [s for s in staff_list if not s['attendance']]
        else:
            staff_list = [s for s in staff_list if s['status'] == status_filter]
    
    # Calculate summary counts
    present_count = 0
    absent_count = 0
    late_count = 0
    leave_count = 0
    half_day_count = 0
    
    for item in staff_list:
        if item['status'] == 'present':
            present_count += 1
        elif item['status'] == 'absent':
            absent_count += 1
        elif item['status'] == 'late':
            late_count += 1
        elif item['status'] == 'leave':
            leave_count += 1
        elif item['status'] == 'half_day':
            half_day_count += 1
    
    total_staff = len(staff_list)
    marked_count = present_count + absent_count + late_count + leave_count + half_day_count
    
    if request.method == 'POST':
        # For POST, we need to save for ALL active staff, not just filtered
        all_staff = StaffMember.objects.filter(employment_status='active')
        if search_query:
            all_staff = all_staff.filter(
                Q(staff_id__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )
        if department_filter:
            all_staff = all_staff.filter(department__icontains=department_filter)
            
        for staff in all_staff:
            status = request.POST.get(f'status_{staff.pk}')
            if status:
                StaffAttendance.objects.update_or_create(
                    staff=staff,
                    date=date_obj,
                    defaults={
                        'status': status,
                        'marked_by': request.user,
                        'remarks': request.POST.get(f'remarks_{staff.pk}', '')
                    }
                )
        messages.success(request, f'Attendance for {date_obj} saved successfully.')
        # Preserve filters after save
        return redirect(f'{request.path}?date={selected_date}&search={search_query}&department={department_filter}&attendance_status={status_filter}')
    
    # Get unique departments for filter
    departments = StaffMember.objects.values_list('department', flat=True).distinct()
    
    context = {
        'staff_list': staff_list,
        'selected_date': selected_date,
        'search_query': search_query,
        'department_filter': department_filter,
        'status_filter': status_filter,
        'departments': departments,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'leave_count': leave_count,
        'half_day_count': half_day_count,
        'total_staff': total_staff,
        'marked_count': marked_count,
        'section': 'staff'
    }
    return render(request, 'staff_management/staff_attendance.html', context)