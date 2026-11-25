from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from accounts.views import is_admin_user
from accounts.dashboard import record_audit_log
from staff_management.models import StaffMember
from ..models import Child, EducationRecord, Course, EducationResult


@login_required(login_url='admin_login')
def education_dashboard(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    education_records = EducationRecord.objects.select_related('child', 'class_teacher')
    
    # Get child scores
    child_scores = {}
    results = EducationResult.objects.select_related('child', 'course').all()
    for result in results:
        if result.child_id not in child_scores:
            child_scores[result.child_id] = []
        child_scores[result.child_id].append(result.score)
    
    child_avg_scores = {}
    for child_id, scores in child_scores.items():
        child_avg_scores[child_id] = sum(scores) / len(scores) if scores else 0

    course_count = Course.objects.count()
    teacher_count = StaffMember.objects.filter(position__icontains='Teacher').count()
    result_count = results.count()
    record_count = education_records.count()
    total_children = Child.objects.count()
    students_tracked = education_records.values('child').distinct().count()
    missing_record_count = max(total_children - students_tracked, 0)

    low_performance_count = sum(1 for score in child_avg_scores.values() if score < 50)
    
    # Attention children
    attention_children = []
    for child_id, avg_score in child_avg_scores.items():
        if avg_score < 50:
            child = Child.objects.get(id=child_id)
            attention_children.append(child)
    attention_records = attention_children[:6]
    
    # Top performers
    top_performer_children = []
    for child_id, avg_score in child_avg_scores.items():
        if avg_score >= 80:
            child = Child.objects.get(id=child_id)
            top_performer_children.append(child)
    top_performers = top_performer_children[:5]
    
    recent_results = results.order_by('-created_at')[:5]
    children_without_records = Child.objects.filter(education_record__isnull=True).order_by('child_id')[:5]
    
    # Grade overview
    grade_display = {
        'class_1': 'Class 1', 'class_2': 'Class 2', 'class_3': 'Class 3',
        'class_4': 'Class 4', 'class_5': 'Class 5', 'class_6': 'Class 6',
        'class_7': 'Class 7', 'class_8': 'Class 8', 'class_9': 'Class 9', 'class_10': 'Class 10'
    }
    
    grade_overview = []
    for grade in ['class_1', 'class_2', 'class_3', 'class_4', 'class_5', 'class_6', 'class_7', 'class_8']:
        records = education_records.filter(grade_level=grade)
        if records.exists():
            total_score = 0
            score_count = 0
            low_perf_count = 0
            for record in records:
                avg_score = child_avg_scores.get(record.child.id, 0)
                total_score += avg_score
                score_count += 1
                if avg_score < 50:
                    low_perf_count += 1
            
            avg_score = total_score / score_count if score_count > 0 else 0
            
            grade_overview.append({
                'grade_level': grade_display.get(grade, grade),
                'student_count': records.count(),
                'record_count': records.count(),
                'avg_score': avg_score,
                'low_performance_count': low_perf_count,
            })

    record_audit_log(request, 'VIEW', 'Education Dashboard', details='Viewed education dashboard')

    context = {
        'course_count': course_count,
        'teacher_count': teacher_count,
        'result_count': result_count,
        'record_count': record_count,
        'total_children': total_children,
        'students_tracked': students_tracked,
        'missing_record_count': missing_record_count,
        'avg_score': sum(child_avg_scores.values()) / len(child_avg_scores) if child_avg_scores else 0,
        'low_performance_count': low_performance_count,
        'attention_records': attention_records,
        'top_performers': top_performers,
        'recent_results': recent_results,
        'children_without_records': children_without_records,
        'grade_overview': grade_overview,
    }
    return render(request, 'children/education_dashboard.html', context)


@login_required(login_url='admin_login')
def education_class_overview(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    education_records = EducationRecord.objects.select_related('child')
    
    # Get child scores
    child_scores = {}
    results = EducationResult.objects.all()
    for result in results:
        if result.child_id not in child_scores:
            child_scores[result.child_id] = []
        child_scores[result.child_id].append(result.score)
    
    child_avg_scores = {}
    for child_id, scores in child_scores.items():
        child_avg_scores[child_id] = sum(scores) / len(scores) if scores else 0

    grade_display = {
        'class_1': 'Class 1', 'class_2': 'Class 2', 'class_3': 'Class 3',
        'class_4': 'Class 4', 'class_5': 'Class 5', 'class_6': 'Class 6',
        'class_7': 'Class 7', 'class_8': 'Class 8', 'class_9': 'Class 9', 'class_10': 'Class 10'
    }
    
    class_summary = []
    for grade in ['class_1', 'class_2', 'class_3', 'class_4', 'class_5', 'class_6', 'class_7', 'class_8']:
        records = education_records.filter(grade_level=grade)
        if records.exists():
            total_score = 0
            score_count = 0
            for record in records:
                avg_score = child_avg_scores.get(record.child.id, 0)
                total_score += avg_score
                score_count += 1
            
            avg_score = total_score / score_count if score_count > 0 else 0
            
            class_summary.append({
                'grade': grade_display.get(grade, grade),
                'student_count': records.count(),
                'record_count': records.count(),
                'avg_score': avg_score,
            })

    totals = education_records.aggregate(
        record_count=Count('pk'),
        student_count=Count('child', distinct=True),
    )
    
    all_scores = list(child_avg_scores.values())
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

    record_audit_log(request, 'VIEW', 'Education Class Overview', details='Viewed education class overview')
    return render(request, 'children/education_class_overview.html', {
        'class_summary': class_summary,
        'total_records': totals['record_count'] or 0,
        'total_students': totals['student_count'] or 0,
        'avg_score': avg_score,
    })


def education_attendance(request):
    from accounts.views import is_admin_user
    from django.contrib import messages
    from django.shortcuts import redirect, render
    from django.db import models
    from ..models import EducationRecord
    
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    education_records = EducationRecord.objects.select_related('child').all()
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    grade_filter = request.GET.get('grade')
    attendance_filter = request.GET.get('attendance_status')
    search_query = request.GET.get('search')
    today = timezone.localdate()
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            education_records = education_records.filter(created_at__date__gte=date_from_obj)
        except:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            education_records = education_records.filter(created_at__date__lte=date_to_obj)
        except:
            pass
    
    if grade_filter and grade_filter != 'all':
        education_records = education_records.filter(grade_level=grade_filter)
    
    if attendance_filter == 'excellent':
        education_records = education_records.filter(attendance_percent__gte=90)
    elif attendance_filter == 'good':
        education_records = education_records.filter(attendance_percent__gte=75, attendance_percent__lt=90)
    elif attendance_filter == 'average':
        education_records = education_records.filter(attendance_percent__gte=60, attendance_percent__lt=75)
    elif attendance_filter == 'low':
        education_records = education_records.filter(attendance_percent__lt=60)
    
    if search_query:
        education_records = education_records.filter(child__full_name__icontains=search_query)
    
    grades = EducationRecord.objects.values_list('grade_level', flat=True).distinct()
    
    total_students = education_records.count()
    excellent_count = education_records.filter(attendance_percent__gte=90).count()
    good_count = education_records.filter(attendance_percent__gte=75, attendance_percent__lt=90).count()
    average_count = education_records.filter(attendance_percent__gte=60, attendance_percent__lt=75).count()
    low_count = education_records.filter(attendance_percent__lt=60).count()
    avg_attendance = education_records.aggregate(avg=models.Avg('attendance_percent'))['avg'] or 0
    
    if not date_from:
        date_from = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = today.strftime('%Y-%m-%d')
    
    context = {
        'education_records': education_records,
        'today': today,
        'date_from': date_from,
        'date_to': date_to,
        'grade_filter': grade_filter,
        'attendance_filter': attendance_filter,
        'search_query': search_query,
        'grades': grades,
        'total_students': total_students,
        'excellent_count': excellent_count,
        'good_count': good_count,
        'average_count': average_count,
        'low_count': low_count,
        'avg_attendance': round(avg_attendance, 1),
        'section': 'education'
    }
    
    if request.GET.get('download') == 'excel':
        return generate_attendance_report_excel(request, context)
    
    return render(request, 'children/education_attendance.html', context)


def generate_attendance_report_excel(request, context):
    import openpyxl
    from django.http import HttpResponse
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Report"
    
    headers = ['Child ID', 'Child Name', 'Grade Level', 'School', 'Roll Number', 'Attendance %', 'Status', 'Academic Year']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
        ws.cell(row=1, column=col).font = openpyxl.styles.Font(bold=True)
    
    for row, record in enumerate(context['education_records'], 2):
        ws.cell(row=row, column=1, value=record.child.child_id)
        ws.cell(row=row, column=2, value=record.child.full_name)
        ws.cell(row=row, column=3, value=record.grade_level)
        ws.cell(row=row, column=4, value=record.school_name)
        ws.cell(row=row, column=5, value=record.roll_number)
        ws.cell(row=row, column=6, value=float(record.attendance_percent))
        
        attendance = record.attendance_percent
        if attendance >= 90:
            status = 'Excellent'
        elif attendance >= 75:
            status = 'Good'
        elif attendance >= 60:
            status = 'Average'
        else:
            status = 'Low - Needs Attention'
        ws.cell(row=row, column=7, value=status)
        ws.cell(row=row, column=8, value=record.academic_year)
    
    for col in range(1, 9):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 20
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.xlsx"'
    wb.save(response)
    return response