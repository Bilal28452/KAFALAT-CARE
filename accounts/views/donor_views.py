from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.middleware.csrf import get_token

from accounts.dashboard import record_audit_log
from accounts.forms import AdminLoginForm, AdminSignupForm
from accounts.models import AccountProfile
from donations.forms import DonorDonationForm
from donations.models import Donation


def is_donor_user(user):
    return hasattr(user, 'account_profile') and user.account_profile.role == AccountProfile.ROLE_DONOR


@never_cache
def donor_signup(request):
    get_token(request)
    if request.method == 'POST':
        data = request.POST.copy()
        data['role'] = AccountProfile.ROLE_DONOR
        form = AdminSignupForm(data)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Your donor account has been created.')
            return redirect('donor_dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminSignupForm(initial={'role': AccountProfile.ROLE_DONOR})

    return render(request, 'accounts/donor_signup.html', {
        'form': form,
        'selected_role': AccountProfile.ROLE_DONOR,
    })


@never_cache
def donor_login(request):
    get_token(request)
    if request.method == 'POST':
        data = request.POST.copy()
        data['role'] = AccountProfile.ROLE_DONOR
        form = AdminLoginForm(request, data)
        if form.is_valid():
            login(request, form.user, backend='django.contrib.auth.backends.ModelBackend')
            if not form.cleaned_data.get('remember'):
                request.session.set_expiry(0)
            messages.success(request, 'Signed in successfully.')
            return redirect('donor_dashboard')
        messages.error(request, 'Invalid login credentials.')
    else:
        form = AdminLoginForm(initial={'role': AccountProfile.ROLE_DONOR})

    return render(request, 'accounts/donor_login.html', {
        'form': form,
        'selected_role': AccountProfile.ROLE_DONOR,
    })


def donor_logout(request):
    logout(request)
    messages.success(request, 'Signed out successfully.')
    return redirect('donor_login')


def donor_dashboard_context(request):
    today = timezone.localdate()
    donations = Donation.objects.filter(donor=request.user).order_by('-donated_at', '-created_at')
    completed = donations.filter(status='completed')

    total_given = completed.aggregate(total=Sum('amount'))['total'] or 0
    monthly_given = completed.filter(donated_at__year=today.year, donated_at__month=today.month).aggregate(total=Sum('amount'))['total'] or 0
    donor_name = request.user.get_full_name() or request.user.username
    initials = ''.join(part[0] for part in donor_name.split()[:2]).upper() or 'DN'

    nav_items = [
        {'id': 'overview', 'label': 'Overview', 'icon': 'bi bi-speedometer2', 'url': '/accounts/donor/dashboard/?section=overview'},
        {'id': 'donations', 'label': 'My Donations', 'icon': 'bi bi-gift', 'url': '/accounts/donor/dashboard/?section=donations'},
        {'id': 'receipts', 'label': 'Receipts', 'icon': 'bi bi-receipt', 'url': '/accounts/donor/dashboard/?section=receipts'},
        {'id': 'impact', 'label': 'Impact', 'icon': 'bi bi-heart-pulse', 'url': '/accounts/donor/dashboard/?section=impact'},
        {'id': 'profile', 'label': 'Profile', 'icon': 'bi bi-person-circle', 'url': '/accounts/donor/profile/'},
    ]
    active_section = request.GET.get('section', 'overview')
    if active_section not in {'overview', 'donations', 'receipts', 'impact'}:
        active_section = 'overview'

    return {
        'page_title': 'Donor Dashboard',
        'donor_name': donor_name,
        'admin_name': donor_name,
        'admin_role': 'Donor',
        'user_initials': initials[:2],
        'active_section': active_section,
        'active_nav_item': next((item for item in nav_items if item['id'] == active_section), nav_items[0]),
        'nav_items': nav_items,
        'show_dashboard_nav': True,
        'stats': {
            'total_given': total_given,
            'monthly_given': monthly_given,
            'donation_count': donations.count(),
            'completed_count': completed.count(),
        },
        'donations': donations[:20],
    }


@login_required(login_url='donor_login')
def donor_dashboard(request):
    if not is_donor_user(request.user):
        messages.error(request, 'Only donor accounts can access the donor dashboard.')
        return redirect('index')
    record_audit_log(request, 'VIEW', 'Donor Dashboard', details='Viewed donor dashboard')
    return render(request, 'accounts/donor_dashboard.html', donor_dashboard_context(request))


@login_required(login_url='donor_login')
def donor_donation_create(request):
    if not is_donor_user(request.user):
        messages.error(request, 'Only donor accounts can submit donations.')
        return redirect('index')

    if request.method == 'POST':
        form = DonorDonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = request.user
            donation.donor_name = request.user.get_full_name() or request.user.username
            donation.status = 'pending'
            donation.save()
            record_audit_log(request, 'CREATE', 'Donations', record_id=str(donation.pk), details='Submitted a donation')
            messages.success(request, 'Your donation has been submitted successfully.')
            return redirect('donor_donation_detail', pk=donation.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = DonorDonationForm(initial={'donated_at': timezone.localdate()})

    return render(request, 'accounts/donor_donation_form.html', {
        'form': form,
        'show_dashboard_nav': True,
        'nav_items': donor_dashboard_context(request)['nav_items'],
        'active_section': 'donations',
        'donor_name': request.user.get_full_name() or request.user.username,
        'admin_name': request.user.get_full_name() or request.user.username,
        'admin_role': 'Donor',
        'user_initials': (request.user.get_full_name() or request.user.username)[:2].upper(),
        'page_title': 'Make a Donation',
    })


@login_required(login_url='donor_login')
def donor_donation_list(request):
    if not is_donor_user(request.user):
        return redirect('index')
    donations = Donation.objects.filter(donor=request.user).order_by('-donated_at', '-created_at')
    context = donor_dashboard_context(request)
    context.update({'active_section': 'donations', 'donations': donations, 'page_title': 'My Donations'})
    return render(request, 'accounts/donor_donation_list.html', context)


@login_required(login_url='donor_login')
def donor_donation_detail(request, pk):
    if not is_donor_user(request.user):
        return redirect('index')
    donation = get_object_or_404(Donation, pk=pk, donor=request.user)
    record_audit_log(request, 'VIEW', 'Donations', record_id=str(donation.pk), details='Viewed donation details')
    context = donor_dashboard_context(request)
    context.update({'active_section': 'donations', 'donation': donation, 'page_title': 'Donation Details'})
    return render(request, 'accounts/donor_donation_detail.html', context)


@login_required(login_url='donor_login')
def donor_profile(request):
    if not is_donor_user(request.user):
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
        return redirect('donor_profile')

    context = donor_dashboard_context(request)
    context.update({'active_section': 'profile', 'page_title': 'My Profile'})
    return render(request, 'accounts/donor_profile.html', context)


@login_required(login_url='donor_login')
def donor_change_password(request):
    if not is_donor_user(request.user):
        return redirect('index')
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('donor_profile')
        messages.error(request, 'Please correct the password errors below.')
    else:
        form = PasswordChangeForm(request.user)
    context = donor_dashboard_context(request)
    context.update({'form': form, 'active_section': 'profile', 'page_title': 'Change Password'})
    return render(request, 'accounts/donor_change_password.html', context)
