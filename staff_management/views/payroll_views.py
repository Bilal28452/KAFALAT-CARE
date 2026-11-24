from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime

from accounts.views.auth_views import is_admin_user
from accounts.dashboard import record_audit_log
from ..models import StaffMember, SalaryRecord


@login_required(login_url='admin_login')
def staff_payroll(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    # Get filter parameters
    month_filter = request.GET.get('month', '')
    year_filter = request.GET.get('year', '')
    staff_search = request.GET.get('staff_search', '')
    payment_status_filter = request.GET.get('payment_status', '')
    
    # Convert to int if provided
    month_filter_int = int(month_filter) if month_filter and month_filter.isdigit() else None
    year_filter_int = int(year_filter) if year_filter and year_filter.isdigit() else None
    
    # Get salaries with filters
    salaries = SalaryRecord.objects.select_related('staff__user').all()
    
    if month_filter_int:
        salaries = salaries.filter(month=month_filter_int)
    if year_filter_int:
        salaries = salaries.filter(year=year_filter_int)
    if payment_status_filter:
        salaries = salaries.filter(payment_status=payment_status_filter)
    
    # Staff search
    staff_salary_history = None
    staff_name = None
    selected_staff = None
    
    if staff_search:
        staff_members = StaffMember.objects.filter(
            Q(staff_id__icontains=staff_search) |
            Q(user__first_name__icontains=staff_search) |
            Q(user__last_name__icontains=staff_search) |
            Q(user__username__icontains=staff_search)
        )
        if staff_members.exists():
            selected_staff = staff_members.first()
            staff_name = selected_staff.user.get_full_name() or selected_staff.user.username
            staff_salary_history = SalaryRecord.objects.filter(staff=selected_staff).order_by('-year', '-month')
            salaries = salaries.filter(staff=selected_staff)
    
    # Staff without salary for selected month/year
    staff_without_salary = []
    if month_filter_int and year_filter_int:
        # Get all active staff
        all_active_staff = StaffMember.objects.filter(employment_status='active')
        # Get staff IDs that have salary for this month/year
        staff_with_salary_ids = SalaryRecord.objects.filter(
            month=month_filter_int, 
            year=year_filter_int
        ).values_list('staff_id', flat=True)
        # Exclude those who already have salary
        staff_without_salary = all_active_staff.exclude(id__in=staff_with_salary_ids)
    
    # Get current year
    current_year = datetime.now().year
    months = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'),
              (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]
    
    context = {
        'salaries': salaries,
        'staff_without_salary': staff_without_salary,
        'month_filter': month_filter,
        'year_filter': year_filter,
        'staff_search': staff_search,
        'payment_status_filter': payment_status_filter,
        'staff_salary_history': staff_salary_history,
        'staff_name': staff_name,
        'selected_staff': selected_staff,
        'months': months,
        'years': [current_year],  # Only current year
        'section': 'staff'
    }
    return render(request, 'staff_management/staff_payroll.html', context)


@login_required(login_url='admin_login')
def staff_payroll_create(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    from decimal import Decimal
    from datetime import datetime
    
    if request.method == 'POST':
        staff_id = request.POST.get('staff')
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))
        
        staff = get_object_or_404(StaffMember, pk=staff_id)
        
        # Check if salary already exists
        existing = SalaryRecord.objects.filter(staff=staff, month=month, year=year).first()
        if existing:
            messages.warning(request, f'Salary record already exists for {staff.user.get_full_name()} in {month}/{year}')
            return redirect('staff_payroll')
        
        SalaryRecord.objects.create(
            staff=staff,
            month=month,
            year=year,
            base_salary=Decimal(str(request.POST.get('base_salary', 0))),
            attendance_bonus=Decimal(str(request.POST.get('attendance_bonus', 0))),
            overtime_pay=Decimal(str(request.POST.get('overtime_pay', 0))),
            deductions=Decimal(str(request.POST.get('deductions', 0))),
            advances=Decimal(str(request.POST.get('advances', 0))),
            payment_status=request.POST.get('payment_status', 'pending'),
            notes=request.POST.get('notes', '')
        )
        messages.success(request, f'Salary record created for {staff.user.get_full_name()}.')
        return redirect('staff_payroll')
    
    # GET request - provide default values
    staff_id = request.GET.get('staff')
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Safely convert month and year parameters
    try:
        month = int(request.GET.get('month', current_month))
    except (ValueError, TypeError):
        month = current_month
    
    try:
        year = int(request.GET.get('year', current_year))
    except (ValueError, TypeError):
        year = current_year
    
    staff_members = StaffMember.objects.filter(employment_status='active')
    months = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'),
              (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]
    
    context = {
        'staff_members': staff_members,
        'selected_staff': staff_id,
        'month': month,
        'year': year,
        'months': months,
        'years': [current_year],
        'section': 'staff'
    }
    return render(request, 'staff_management/staff_payroll_form.html', context)

@login_required(login_url='admin_login')
def staff_payroll_edit(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    from decimal import Decimal
    from datetime import datetime
    
    salary = get_object_or_404(SalaryRecord, pk=pk)
    staff_members = StaffMember.objects.filter(employment_status='active')
    
    if request.method == 'POST':
        salary.base_salary = Decimal(str(request.POST.get('base_salary', 0)))
        salary.attendance_bonus = Decimal(str(request.POST.get('attendance_bonus', 0)))
        salary.overtime_pay = Decimal(str(request.POST.get('overtime_pay', 0)))
        salary.deductions = Decimal(str(request.POST.get('deductions', 0)))
        salary.advances = Decimal(str(request.POST.get('advances', 0)))
        salary.payment_status = request.POST.get('payment_status')
        salary.notes = request.POST.get('notes', '')
        salary.month = int(request.POST.get('month'))
        salary.year = int(request.POST.get('year'))
        if request.POST.get('payment_date'):
            salary.payment_date = datetime.strptime(request.POST.get('payment_date'), '%Y-%m-%d').date()
        salary.save()
        messages.success(request, 'Salary record updated.')
        return redirect('staff_payroll')
    
    current_year = datetime.now().year
    months = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'),
              (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]
    
    context = {
        'salary': salary,
        'staff_members': staff_members,
        'months': months,
        'years': [current_year],  # Only current year
        'section': 'staff'
    }
    return render(request, 'staff_management/staff_payroll_form.html', context)