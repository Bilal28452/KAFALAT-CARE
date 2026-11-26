import re
import calendar
from datetime import date

from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.middleware.csrf import get_token
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from accounts.dashboard import record_audit_log
from accounts.forms import AdminLoginForm, AdminSignupForm
from accounts.models import AccountProfile
from children.models import Child
from payments.models import Payment
from payments.services import has_verified_sponsorship_payment
from sponsorships.forms import SponsorMessageForm
from sponsorships.models import Sponsorship, SponsorshipConversation
from sponsorships.communication_context import communication_activity
from sponsorships.notifications import notify_users


def is_sponsor_user(user):
    return hasattr(user, 'account_profile') and user.account_profile.role == AccountProfile.ROLE_SPONSOR


class SponsorApplicationForm(forms.Form):
    monthly_amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=1, label='Maximum Monthly Sponsorship (PKR)', widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '0.01'}))
    start_date = forms.DateField(initial=timezone.localdate, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    phone = forms.CharField(max_length=30, label='Phone Number', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92 XXX XXXXXXX'}))
    cnic = forms.CharField(max_length=20, label='CNIC', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345-1234567-1'}))
    terms_accepted = forms.BooleanField(
        required=True,
        label='I agree to the sponsorship terms and privacy policy',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def clean_cnic(self):
        value = self.cleaned_data['cnic'].strip()
        match = re.fullmatch(r'(\d{5})-?(\d{7})-?(\d)', value)
        if not match:
            raise forms.ValidationError('Enter a valid 13-digit CNIC.')
        return f'{match.group(1)}-{match.group(2)}-{match.group(3)}'

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not re.fullmatch(r'\+?[\d\s()-]{7,30}', phone):
            raise forms.ValidationError('Enter a valid phone number.')
        digit_count = sum(character.isdigit() for character in phone)
        if not 7 <= digit_count <= 15:
            raise forms.ValidationError('Phone number must contain between 7 and 15 digits.')
        return phone

    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        if start_date < timezone.localdate():
            raise forms.ValidationError('The sponsorship start date cannot be in the past.')
        return start_date


def add_calendar_month(value):
    month_index = value.month
    year = value.year + (month_index // 12)
    month = (month_index % 12) + 1
    return date(year, month, min(value.day, calendar.monthrange(year, month)[1]))


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
    return redirect('login')


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
    verified_payment = Payment.objects.filter(
        sponsorship_id=OuterRef('pk'),
        status=Payment.STATUS_PAID,
    )
    sponsorships = Sponsorship.objects.filter(sponsor=request.user).annotate(
        has_verified_payment=Exists(verified_payment),
    ).select_related('child').order_by('-start_date', '-created_at')
    active = sponsorships.filter(status='active')
    can_request_sponsorship = not sponsorships.filter(
        status__in=['pending', 'active', 'paused'],
    ).exists()
    monthly_commitment = active.aggregate(total=Sum('monthly_amount'))['total'] or 0
    sponsor_name = request.user.get_full_name() or request.user.username
    initials = ''.join(part[0] for part in sponsor_name.split()[:2]).upper() or 'SP'

    nav_items = [
        {'id': 'overview', 'label': 'Overview', 'icon': 'bi bi-speedometer2', 'url': '/accounts/sponsor/dashboard/?section=overview'},
        {'id': 'my_sponsorships', 'label': 'My Sponsorships', 'icon': 'bi bi-heart', 'url': '/accounts/sponsor/dashboard/?section=my_sponsorships'},
        {'id': 'payments', 'label': 'Payments', 'icon': 'bi bi-credit-card', 'url': '/accounts/sponsor/dashboard/?section=payments'},
        {'id': 'profile', 'label': 'Profile', 'icon': 'bi bi-person-circle', 'url': '/accounts/sponsor/profile/'},
    ]
    active_section = request.GET.get('section', 'overview')
    if active_section not in {'overview', 'my_sponsorships', 'payments'}:
        active_section = 'overview'

    available_children = Child.objects.filter(sponsor_status='available').order_by('child_id')
    payment_transactions = Payment.objects.filter(
        sponsorship__sponsor=request.user,
    ).select_related('sponsorship')
    approved_sponsorship = active.filter(
        child__isnull=False,
        has_verified_payment=True,
    ).select_related('child').first()
    child_progress = None
    if approved_sponsorship:
        child = approved_sponsorship.child
        child_progress = {
            'sponsorship': approved_sponsorship,
            'child': child,
        }

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
        'can_request_sponsorship': can_request_sponsorship,
        'child_progress': child_progress,
        'payment_transactions': payment_transactions,
        'available_children': available_children,
        **communication_activity(request.user),
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

    active_sponsorship = get_object_or_404(
        Sponsorship.objects.select_related('child'),
        sponsor=request.user,
        child_id=pk,
        status='active',
    )
    if not has_verified_sponsorship_payment(active_sponsorship):
        context = sponsor_dashboard_context(request)
        context.update({
            'active_section': 'my_sponsorships',
            'active_sponsorship': active_sponsorship,
            'page_title': 'First Payment Required',
        })
        return render(request, 'accounts/sponsor_payment_required.html', context)

    child = active_sponsorship.child
    is_approved_sponsor = True
    conversations = []
    message_form = None

    if active_sponsorship:
        conversations = active_sponsorship.conversations.select_related('staff__user')
        message_form = SponsorMessageForm()
        sponsorship_payments = active_sponsorship.payment_transactions.all()
    else:
        sponsorship_payments = []

    context = sponsor_dashboard_context(request)
    context.update({
        'active_section': 'my_sponsorships',
        'child': child,
        'is_approved_sponsor': is_approved_sponsor,
        'active_sponsorship': active_sponsorship,
        'has_verified_payment': True,
        'today': timezone.localdate(),
        'conversations': conversations,
        'message_form': message_form,
        'sponsorship_payments': sponsorship_payments,
        'child_match_score': ai_match_score(child),
        'page_title': 'Child Profile',
    })
    return render(request, 'accounts/sponsor_child_detail.html', context)


def _sponsor_tracking_page(request, child_id, tracking_section):
    sponsorship = get_object_or_404(
        Sponsorship.objects.select_related('child').filter(
            payment_transactions__status=Payment.STATUS_PAID,
        ).distinct(),
        sponsor=request.user,
        child_id=child_id,
        status='active',
    )
    child = sponsorship.child
    context = sponsor_dashboard_context(request)
    context.update({
        'active_section': 'my_sponsorships',
        'active_sponsorship': sponsorship,
        'child': child,
        'tracking_section': tracking_section,
    })

    if tracking_section == 'health':
        context.update({
            'page_title': 'Health Tracking',
            'latest_health': child.health_records.first(),
            'health_records': child.health_records.all()[:30],
        })
    elif tracking_section == 'education':
        context.update({
            'page_title': 'Education Tracking',
            'education': getattr(child, 'education_record', None),
            'education_results': child.education_results.select_related(
                'course',
                'teacher',
            ).order_by('-created_at')[:30],
            'attendances': child.attendances.order_by('-date')[:30],
        })
    else:
        context.update({
            'page_title': 'Meal Tracking',
            'meals': child.meal_records.order_by('-date')[:30],
        })
    return render(request, 'accounts/sponsor_tracking_page.html', context)


@login_required(login_url='sponsor_login')
def sponsor_health_tracking(request, pk):
    if not is_sponsor_user(request.user):
        return redirect('index')
    return _sponsor_tracking_page(request, pk, 'health')


@login_required(login_url='sponsor_login')
def sponsor_education_tracking(request, pk):
    if not is_sponsor_user(request.user):
        return redirect('index')
    return _sponsor_tracking_page(request, pk, 'education')


@login_required(login_url='sponsor_login')
def sponsor_meal_tracking(request, pk):
    if not is_sponsor_user(request.user):
        return redirect('index')
    return _sponsor_tracking_page(request, pk, 'meal')


@login_required(login_url='sponsor_login')
def sponsor_application(request):
    if not is_sponsor_user(request.user):
        return redirect('index')

    if Sponsorship.objects.filter(
        sponsor=request.user,
        status__in=['pending', 'active', 'paused'],
    ).exists():
        messages.info(request, 'Your account already has a pending or current sponsorship. One child may be sponsored per account at a time.')
        return redirect('sponsor_dashboard')

    if request.method == 'POST':
        form = SponsorApplicationForm(request.POST)
        if form.is_valid():
            code = f'SP-{timezone.localdate().year}-{Sponsorship.objects.count() + 1:04d}'
            while Sponsorship.objects.filter(sponsor_code=code).exists():
                code = f'SP-{timezone.localdate().year}-{Sponsorship.objects.count() + 10001:04d}'

            profile = request.user.account_profile
            profile.phone = form.cleaned_data['phone']
            profile.cnic = form.cleaned_data['cnic']
            try:
                with transaction.atomic():
                    profile.save(update_fields=['phone', 'cnic', 'updated_at'])
                    sponsorship = Sponsorship.objects.create(
                        sponsor=request.user,
                        sponsor_code=code,
                        sponsor_name=request.user.get_full_name() or request.user.username,
                        cnic=form.cleaned_data['cnic'],
                        phone=form.cleaned_data['phone'],
                        email=request.user.email,
                        child=None,
                        monthly_amount=form.cleaned_data['monthly_amount'],
                        start_date=form.cleaned_data['start_date'],
                        next_payment_date=form.cleaned_data['start_date'],
                        status='pending',
                        ai_match_score=0,
                        agreement_accepted_at=timezone.now(),
                        agreement_version='sponsor-terms-v1',
                        minimum_commitment_end_date=add_calendar_month(form.cleaned_data['start_date']),
                    )
            except IntegrityError:
                messages.warning(request, 'Your account already has a pending or current sponsorship. One child may be sponsored per account at a time.')
                return redirect('sponsor_dashboard')
            record_audit_log(request, 'CREATE', 'Sponsorship Requests', record_id=sponsorship.sponsor_code, details='Submitted budget-based sponsorship request')
            admins = request.user.__class__.objects.filter(account_profile__role=AccountProfile.ROLE_ADMIN)
            notify_users(
                [request.user],
                'Sponsorship request submitted',
                'A sponsorship request is awaiting review. Sign in to view the request status.',
                reverse('sponsor_dashboard'),
            )
            notify_users(
                admins,
                'Sponsorship request awaiting review',
                'A new sponsorship request is ready for admin review.',
                reverse('sponsorship_detail', kwargs={'pk': sponsorship.pk}),
            )
            messages.success(request, 'Your sponsorship request was sent to the admin for AI matching and approval.')
            return redirect('sponsor_dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = SponsorApplicationForm(initial={
            'start_date': timezone.localdate(),
            'monthly_amount': 5000,
            'phone': request.user.account_profile.phone,
            'cnic': request.user.account_profile.cnic,
        })

    context = sponsor_dashboard_context(request)
    context.update({'form': form, 'active_section': 'overview', 'page_title': 'Request Sponsorship'})
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
