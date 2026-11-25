from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime

from accounts.views.auth_views import is_admin_user
from ..models import MealSchedule, MealRecord, ChildAllergy
from ..forms import DailyMealLogForm, ChildAllergyForm
from children.models import Child
from staff_management.models import StaffMember


@login_required(login_url='admin_login')
def daily_log(request):
    """Record daily meal consumption for children"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    selected_child = None
    meal_records = {}
    schedules = []
    allergies = None
    
    if request.method == 'POST':
        child_id = request.POST.get('child')
        date_str = request.POST.get('date')
        selected_child = get_object_or_404(Child, pk=child_id)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get schedule for this day
        day_name = date.strftime('%A').lower()
        schedules = MealSchedule.objects.filter(day=day_name, is_active=True)
        
        # Save or update records
        for schedule in schedules:
            status = request.POST.get(f'status_{schedule.meal_type}')
            activity_notes = request.POST.get(f'notes_{schedule.meal_type}', '')
            
            if status:
                MealRecord.objects.update_or_create(
                    child=selected_child,
                    date=date,
                    meal_type=schedule.meal_type,
                    defaults={
                        'scheduled_food': schedule.food_items,
                        'status': status,
                        'activity_notes': activity_notes,
                        'recorded_by': StaffMember.objects.filter(user=request.user).first()
                    }
                )
        messages.success(request, f'Meal records saved for {selected_child.full_name} on {date}')
        return redirect('daily_log')
    
    # GET request
    child_id = request.GET.get('child')
    date_str = request.GET.get('date', timezone.localdate().strftime('%Y-%m-%d'))
    
    if child_id:
        selected_child = get_object_or_404(Child, pk=child_id)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        day_name = date.strftime('%A').lower()
        
        # Get schedules for this day
        schedules = MealSchedule.objects.filter(day=day_name, is_active=True)
        
        # Get existing records
        for schedule in schedules:
            record = MealRecord.objects.filter(
                child=selected_child,
                date=date,
                meal_type=schedule.meal_type
            ).first()
            if record:
                meal_records[schedule.meal_type] = record
        
        # Get allergies
        allergy_obj = ChildAllergy.objects.filter(child=selected_child).first()
        allergies = allergy_obj.allergies if allergy_obj else ''
    
    children = Child.objects.all().order_by('full_name')
    
    context = {
        'selected_child': selected_child,
        'meal_records': meal_records,
        'schedules': schedules,
        'allergies': allergies,
        'date': date_str,
        'children': children,
        'section': 'meals'
    }
    return render(request, 'meals/daily_log.html', context)


@login_required(login_url='admin_login')
def child_allergy_update(request, child_id):
    """Update child allergies"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    child = get_object_or_404(Child, pk=child_id)
    allergy_obj, created = ChildAllergy.objects.get_or_create(child=child)
    
    if request.method == 'POST':
        form = ChildAllergyForm(request.POST, instance=allergy_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Allergies updated for {child.full_name}')
            return redirect('daily_log')
    else:
        form = ChildAllergyForm(instance=allergy_obj)
    
    context = {
        'form': form,
        'child': child,
        'section': 'meals'
    }
    return render(request, 'meals/child_allergy_form.html', context)