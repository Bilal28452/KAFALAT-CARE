from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.middleware.csrf import get_token
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from accounts.dashboard import record_audit_log
from accounts.forms import AdminLoginForm, AdminSignupForm
from accounts.models import AccountProfile
from children.models import Child
from sponsorships.models import Sponsorship


def is_sponsor_user(user):
    return hasattr(user, 'account_profile') and user.account_profile.role == AccountProfile.ROLE_SPONSOR


class SponsorApplicationForm(forms.Form):
    monthly_amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=1, label='Maximum Monthly Sponsorship (PKR)', widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '0.01'}))
    payment_method = forms.CharField(max_length=60, label='Preferred Payment Method', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bank Transfer, JazzCash'}))
    start_date = forms.DateField(initial=timezone.localdate, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@never_cache
def sponsor_signup(request):
    get_token(request)
    if request.method == 'POST':
        data = request.POST.copy()
        data['role'] = AccountProfile.ROLE_SPONSOR
        form = AdminSignupForm(data)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Your sponsor account has been created.')
            return redirect('sponsor_dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminSignupForm(initial={'role': AccountProfile.ROLE_SPONSOR})

    return render(request, 'accounts/sponsor_signup.html', {'form': form, 'selected_role': AccountProfile.ROLE_SPONSOR})


@never_cache
def sponsor_login(request):
    get_token(request)
    if request.method == 'POST':
        data = request.POST.copy()
        data['role'] = AccountProfile.ROLE_SPONSOR
        form = AdminLoginForm(request, data)
        if form.is_valid():
            login(request, form.user, backend='django.contrib.auth.backends.ModelBackend')
            if not form.cleaned_data.get('remember'):
                request.session.set_expiry(0)
            messages.success(request, 'Signed in successfully.')
            return redirect('sponsor_dashboard')
        messages.error(request, 'Invalid login credentials.')
    else:
        form = AdminLoginForm(initial={'role': AccountProfile.ROLE_SPONSOR})

    return render(request, 'accounts/sponsor_login.html', {'form': form, 'selected_role': AccountProfile.ROLE_SPONSOR})


def sponsor_logout(request):
    logout(request)
    messages.success(request, 'Signed out successfully.')
    return redirect('sponsor_login')


def ai_match_score(child):
    """Transparent baseline AI-style match score using available child profile signals."""
    score = 50
    if child.health_status == 'healthy':
        score += 15
    elif child.health_status in {'under_care', 'observation'}:
        score += 8
    if child.education_level:
        score += 15
    if hasattr(child, 'education_record'):
        score += 10
    if child.age:
        score += 10
    return min(score, 98)


def sponsor_dashboard_context(request):
    sponsorships = Sponsorship.objects.filter(sponsor=request.user).select_related('child').order_by('-start_date', '-created_at')
    active = sponsorships.filter(status='active')
    monthly_commitment = active.aggregate(total=Sum('monthly_amount'))['total'] or 0
    sponsor_name = request.user.get_full_name() or request.user.username
    initials = ''.join(part[0] for part in sponsor_name.split()[:2]).upper() or 'SP'

    nav_items = [
        {'id': 'overview', 'label': 'Overview', 'icon': 'bi bi-speedometer2', 'url': '/accounts/sponsor/dashboard/?section=overview'},
        {'id': 'my_sponsorships', 'label': 'My Sponsorships', 'icon': 'bi bi-heart', 'url': '/accounts/sponsor/dashboard/?section=my_sponsorships'},
        {'id': 'children', 'label': 'Sponsorship Request', 'icon': 'bi bi-people', 'url': '/accounts/sponsor/dashboard/?section=children'},
        {'id': 'ai_match', 'label': 'AI Matching', 'icon': 'bi bi-stars', 'url': '/accounts/sponsor/dashboard/?section=ai_match'},
        {'id': 'payments', 'label': 'Payments', 'icon': 'bi bi-credit-card', 'url': '/accounts/sponsor/dashboard/?section=payments'},
        {'id': 'profile', 'label': 'Profile', 'icon': 'bi bi-person-circle', 'url': '/accounts/sponsor/profile/'},
    ]
    active_section = request.GET.get('section', 'overview')
    if active_section not in {'overview', 'my_sponsorships', 'children', 'ai_match', 'payments'}:
        active_section = 'overview'

    available_children = Child.objects.filter(sponsor_status='available').order_by('child_id')
    matches = [{'child': child, 'score': ai_match_score(child)} for child in available_children[:12]]

    return {
        'page_title': 'Sponsor Dashboard',
        'sponsor_name': sponsor_name,
        'donor_name': sponsor_name,
        'admin_name': sponsor_name,
        'admin_role': 'Sponsor',
        'user_initials': initials[:2],
        'active_section': active_section,
        'active_nav_item': next((item for item in nav_items if item['id'] == active_section), nav_items[0]),
        'nav_items': nav_items,
        'show_dashboard_nav': True,
        'sponsorships': sponsorships,
        'active_sponsorships': active,
        'available_children': available_children,
        'ai_matches': matches,
        'stats': {
            'total_sponsorships': sponsorships.count(),
            'active_sponsorships': active.count(),
            'monthly_commitment': monthly_commitment,
            'available_children': available_children.count(),
        },
    }


@login_required(login_url='sponsor_login')
def sponsor_dashboard(request):
    if not is_sponsor_user(request.user):
        messages.error(request, 'Only sponsor accounts can access the sponsor dashboard.')
        return redirect('index')
    record_audit_log(request, 'VIEW', 'Sponsor Dashboard', details='Viewed sponsor dashboard')
    return render(request, 'accounts/sponsor_dashboard.html', sponsor_dashboard_context(request))


@login_required(login_url='sponsor_login')
def sponsor_child_detail(request, pk):
    if not is_sponsor_user(request.user):
        return redirect('index')

    child = get_object_or_404(Child, pk=pk)
    is_approved_sponsor = Sponsorship.objects.filter(sponsor=request.user, child=child, status='active').exists()

    latest_health = child.health_records.first() if hasattr(child, 'health_records') else None
    education = getattr(child, 'education_record', None)
    education_results = child.education_results.select_related('course', 'teacher').order_by('-created_at')[:8] if hasattr(child, 'education_results') else []
    attendances = child.attendances.order_by('-date')[:30] if hasattr(child, 'attendances') else []
    meals = child.meal_records.order_by('-date')[:20] if hasattr(child, 'meal_records') else []

    context = sponsor_dashboard_context(request)
    context.update({
        'active_section': 'children',
        'child': child,
        'is_approved_sponsor': is_approved_sponsor,
        'latest_health': latest_health,
        'education': education,
        'education_results': education_results,
        'attendances': attendances,
        'meals': meals,
        'child_match_score': ai_match_score(child),
        'page_title': 'Child Profile',
    })
    return render(request, 'accounts/sponsor_child_detail.html', context)


@login_required(login_url='sponsor_login')
def sponsor_application(request):
    if not is_sponsor_user(request.user):
        return redirect('index')

    if request.method == 'POST':
        form = SponsorApplicationForm(request.POST)
        if form.is_valid():
            existing = Sponsorship.objects.filter(sponsor=request.user, status='pending').first()
            if existing:
                messages.warning(request, 'You already have a sponsorship request awaiting admin review.')
                return redirect('sponsor_dashboard')

            code = f'SP-{timezone.localdate().year}-{Sponsorship.objects.count() + 1:04d}'
            while Sponsorship.objects.filter(sponsor_code=code).exists():
                code = f'SP-{timezone.localdate().year}-{Sponsorship.objects.count() + 10001:04d}'

            sponsorship = Sponsorship.objects.create(
                sponsor=request.user,
                sponsor_code=code,
                sponsor_name=request.user.get_full_name() or request.user.username,
                cnic=request.user.account_profile.cnic,
                phone=request.user.account_profile.phone,
                email=request.user.email,
                child=None,
                monthly_amount=form.cleaned_data['monthly_amount'],
                start_date=form.cleaned_data['start_date'],
                payment_method=form.cleaned_data['payment_method'],
                next_payment_date=form.cleaned_data['start_date'],
                status='pending',
                ai_match_score=0,
            )
            record_audit_log(request, 'CREATE', 'Sponsorship Requests', record_id=sponsorship.sponsor_code, details='Submitted budget-based sponsorship request')
            messages.success(request, 'Your sponsorship request was sent to the admin for AI matching and approval.')
            return redirect('sponsor_dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = SponsorApplicationForm(initial={'start_date': timezone.localdate(), 'monthly_amount': 5000})

    context = sponsor_dashboard_context(request)
    context.update({'form': form, 'active_section': 'children', 'page_title': 'Request Sponsorship'})
    return render(request, 'accounts/sponsor_application.html', context)


@login_required(login_url='sponsor_login')
def sponsor_profile(request):
    if not is_sponsor_user(request.user):
        return redirect('index')

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        profile = request.user.account_profile
        profile.phone = request.POST.get('phone', '')
        profile.cnic = request.POST.get('cnic', '')
        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('sponsor_profile')

    context = sponsor_dashboard_context(request)
    context.update({'active_section': 'profile', 'page_title': 'My Profile'})
    return render(request, 'accounts/sponsor_profile.html', context)


@login_required(login_url='sponsor_login')
def sponsor_change_password(request):
    if not is_sponsor_user(request.user):
        return redirect('index')
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('sponsor_profile')
        messages.error(request, 'Please correct the password errors below.')
    else:
        form = PasswordChangeForm(request.user)
    context = sponsor_dashboard_context(request)
    context.update({'form': form, 'active_section': 'profile', 'page_title': 'Change Password'})
    return render(request, 'accounts/sponsor_change_password.html', context)
