from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from datetime import datetime, timedelta

from accounts.views.auth_views import is_admin_user
from ..models import MealRecord, ChildAllergy
from children.models import Child


@login_required(login_url='admin_login')
def meal_reports(request):
    """View meal consumption reports and AI risk analysis"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    children = Child.objects.all().order_by('full_name')
    selected_child = None
    meal_stats = {}
    risk_score = 0
    risk_reasons = []
    eating_trend = []
    
    child_id = request.GET.get('child')
    if child_id:
        selected_child = get_object_or_404(Child, pk=child_id)
        
        # Get last 30 days of records
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        records = MealRecord.objects.filter(
            child=selected_child,
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Calculate statistics
        total_meals = records.count()
        ate_fully = records.filter(status='ate_fully').count()
        partially_ate = records.filter(status='partially_ate').count()
        refused = records.filter(status='refused').count()
        absent = records.filter(status='absent').count()
        
        # Most skipped meal
        most_skipped = records.filter(status='refused').values('meal_type').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        # Consecutive refusal days
        refusal_dates = records.filter(status='refused').values_list('date', flat=True).distinct()
        consecutive_refusals = 0
        max_consecutive = 0
        last_date = None
        
        for date in sorted(refusal_dates):
            if last_date and (date - last_date).days == 1:
                consecutive_refusals += 1
            else:
                consecutive_refusals = 1
            max_consecutive = max(max_consecutive, consecutive_refusals)
            last_date = date
        
        # AI Risk Score Calculation
        risk_score = 0
        risk_reasons = []
        
        if total_meals > 0:
            refusal_rate = (refused / total_meals) * 100
            partial_rate = (partially_ate / total_meals) * 100
            
            if refusal_rate > 30:
                risk_score += 40
                risk_reasons.append(f"Refused meals {refusal_rate:.0f}% of the time")
            elif refusal_rate > 15:
                risk_score += 20
                risk_reasons.append(f"Refused meals {refusal_rate:.0f}% of the time")
            
            if max_consecutive >= 5:
                risk_score += 30
                risk_reasons.append(f"Refused meals for {max_consecutive} consecutive days")
            elif max_consecutive >= 3:
                risk_score += 15
                risk_reasons.append(f"Refused meals for {max_consecutive} consecutive days")
            
            if partial_rate > 40:
                risk_score += 15
                risk_reasons.append("Frequently eats partially")
            
            # Check allergies
            allergy_obj = ChildAllergy.objects.filter(child=selected_child).first()
            if allergy_obj and allergy_obj.allergies:
                risk_score += 10
                risk_reasons.append("Has food allergies - monitor reactions")
        
        risk_score = min(risk_score, 100)
        
        # Eating trend (weekly data for chart)
        for i in range(4):
            week_start = end_date - timedelta(days=(i+1)*7)
            week_end = end_date - timedelta(days=i*7)
            week_records = records.filter(date__gte=week_start, date__lte=week_end)
            week_total = week_records.count()
            if week_total > 0:
                week_ate = week_records.filter(status='ate_fully').count()
                eating_trend.append({
                    'week': f'Week {4-i}',
                    'ate_percentage': (week_ate / week_total) * 100
                })
        
        meal_stats = {
            'total_meals': total_meals,
            'ate_fully': ate_fully,
            'partially_ate': partially_ate,
            'refused': refused,
            'absent': absent,
            'ate_percentage': (ate_fully / total_meals * 100) if total_meals > 0 else 0,
            'most_skipped_meal': most_skipped,
            'max_consecutive_refusals': max_consecutive,
        }
    
    context = {
        'children': children,
        'selected_child': selected_child,
        'meal_stats': meal_stats,
        'risk_score': risk_score,
        'risk_reasons': risk_reasons,
        'risk_level': 'High' if risk_score >= 60 else 'Medium' if risk_score >= 30 else 'Low',
        'risk_color': 'danger' if risk_score >= 60 else 'warning' if risk_score >= 30 else 'success',
        'eating_trend': eating_trend,
        'section': 'meals'
    }
    return render(request, 'meals/meal_reports.html', context)