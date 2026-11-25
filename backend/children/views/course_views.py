from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count

from accounts.views import is_admin_user
from accounts.dashboard import record_audit_log
from ..models import Course
from ..forms import CourseForm


@login_required(login_url='admin_login')
def course_list(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    courses = Course.objects.annotate(result_count=Count('results')).order_by('code')
    record_audit_log(request, 'VIEW', 'Courses', details='Viewed courses list')
    return render(request, 'children/course_list.html', {'courses': courses})


@login_required(login_url='admin_login')
def course_create(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            record_audit_log(request, 'CREATE', 'Courses', record_id=str(course.pk), details=f'Created course {course}')
            messages.success(request, f'Course {course} created successfully.')
            return redirect('course_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm()

    return render(request, 'children/course_form.html', {'form': form, 'action': 'Create'})


@login_required(login_url='admin_login')
def course_detail(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    course = get_object_or_404(Course, pk=pk)
    record_audit_log(request, 'VIEW', 'Courses', record_id=str(course.pk), details=f'Viewed course {course}')
    return render(request, 'children/course_detail.html', {'course': course})


@login_required(login_url='admin_login')
def course_update(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            record_audit_log(request, 'UPDATE', 'Courses', record_id=str(course.pk), details=f'Updated course {course}')
            messages.success(request, f'Course {course} updated successfully.')
            return redirect('course_detail', pk=course.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm(instance=course)

    return render(request, 'children/course_form.html', {'form': form, 'action': 'Update', 'course': course})


@login_required(login_url='admin_login')
def course_delete(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        record_audit_log(request, 'DELETE', 'Courses', record_id=str(pk), details=f'Deleted course {course}')
        messages.success(request, f'Course {course} deleted successfully.')
        return redirect('course_list')

    return render(request, 'children/course_confirm_delete.html', {'course': course})