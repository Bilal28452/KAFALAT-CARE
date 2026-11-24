from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from accounts.views.auth_views import is_admin_user
from ..models import MealSchedule
from ..forms import MealScheduleForm


@login_required(login_url='admin_login')
def meal_schedule(request):
    """View and manage meal schedules"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    schedules = MealSchedule.objects.all().order_by('day', 'meal_type')
    
    # Group by day
    grouped_schedules = {}
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_labels = {
        'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
        'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday', 'sunday': 'Sunday'
    }
    
    for day in days:
        grouped_schedules[day] = {
            'label': day_labels[day],
            'breakfast': None,
            'lunch': None,
            'dinner': None,
            'snack': None
        }
    
    for schedule in schedules:
        grouped_schedules[schedule.day][schedule.meal_type] = schedule
    
    context = {
        'grouped_schedules': grouped_schedules,
        'section': 'meals'
    }
    return render(request, 'meals/meal_schedule.html', context)


@login_required(login_url='admin_login')
def meal_schedule_create(request):
    """Create new meal schedule entry"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        form = MealScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Meal schedule added successfully.')
            return redirect('meal_schedule')
    else:
        form = MealScheduleForm()
    
    context = {'form': form, 'action': 'Create', 'section': 'meals'}
    return render(request, 'meals/meal_schedule_form.html', context)


@login_required(login_url='admin_login')
def meal_schedule_edit(request, pk):
    """Edit meal schedule entry"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    schedule = get_object_or_404(MealSchedule, pk=pk)
    
    if request.method == 'POST':
        form = MealScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Meal schedule updated successfully.')
            return redirect('meal_schedule')
    else:
        form = MealScheduleForm(instance=schedule)
    
    context = {'form': form, 'action': 'Update', 'schedule': schedule, 'section': 'meals'}
    return render(request, 'meals/meal_schedule_form.html', context)


@login_required(login_url='admin_login')
def meal_schedule_delete(request, pk):
    """Delete meal schedule entry"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    schedule = get_object_or_404(MealSchedule, pk=pk)
    
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Meal schedule deleted successfully.')
        return redirect('meal_schedule')
    
    context = {'schedule': schedule, 'section': 'meals'}
    return render(request, 'meals/meal_schedule_confirm_delete.html', context)