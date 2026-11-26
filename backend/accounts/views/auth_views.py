from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from ..forms import AdminLoginForm, AdminSignupForm
from ..models import AccountProfile

def get_requested_role(request):
    role = request.GET.get('role')
    valid_roles = {value for value, _ in AccountProfile.ROLE_CHOICES}
    return role if role in valid_roles else AccountProfile.ROLE_ADMIN


def index(request):
    return render(request, 'accounts/index.html')


@never_cache
def register(request):
    # Allow logged-in users to see signup page too
    # if request.user.is_authenticated:
    #     return redirect('dashboard')  # ← Commented out

    if request.method == 'POST':
        form = AdminSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Specify backend to avoid multiple backends error
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully.')
            role = user.account_profile.role
            if role == AccountProfile.ROLE_DONOR:
                return redirect('donor_dashboard')
            if role == AccountProfile.ROLE_SPONSOR:
                return redirect('sponsor_dashboard')
            if role == AccountProfile.ROLE_ADMIN:
                return redirect('dashboard')
            return redirect('dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminSignupForm(initial={'role': get_requested_role(request)})

    return render(request, 'accounts/admin_signup.html', {
        'form': form,
        'role_choices': form.fields['role'].choices,
        'selected_role': form['role'].value() or AccountProfile.ROLE_ADMIN,
    })


@never_cache
def user_login(request):
    # Allow logged-in users to see login page too
    # if request.user.is_authenticated:
    #     return redirect('dashboard')  # ← Commented out

    if request.method == 'POST':
        form = AdminLoginForm(request, request.POST)
        if form.is_valid():
            # Specify backend to avoid multiple backends error
            login(request, form.user, backend='django.contrib.auth.backends.ModelBackend')
            if not form.cleaned_data.get('remember'):
                request.session.set_expiry(0)
            messages.success(request, 'Signed in successfully.')
            role = form.user.account_profile.role
            if role == AccountProfile.ROLE_DONOR:
                return redirect('donor_dashboard')
            if role == AccountProfile.ROLE_SPONSOR:
                return redirect('sponsor_dashboard')
            if role == AccountProfile.ROLE_ADMIN:
                return redirect('dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid login credentials.')
    else:
        form = AdminLoginForm(initial={'role': get_requested_role(request)})

    return render(request, 'accounts/admin_login.html', {
        'form': form,
        'role_choices': form.fields['role'].choices,
        'selected_role': form['role'].value() or AccountProfile.ROLE_ADMIN,
    })


def user_logout(request):
    logout(request)
    messages.success(request, 'Signed out successfully.')
    return redirect('login')


def is_admin_user(user):
    """Check if user is admin (superuser or has admin role)"""
    if user.is_superuser:
        return True
    return hasattr(user, 'account_profile') and user.account_profile.role == AccountProfile.ROLE_ADMIN


def resolve_redirect(request, default_url):
    """Get next URL from request or return default"""
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and next_url.startswith('/'):
        return next_url
    return default_url




@login_required(login_url='admin_login')
def user_profile(request):
    """View and edit user profile"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        # Update profile info
        if hasattr(user, 'account_profile'):
            user.account_profile.phone = request.POST.get('phone', '')
            user.account_profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_profile')
    
    context = {
        'user': request.user,
        'section': 'profile'
    }
    return render(request, 'accounts/user_profile.html', context)


@login_required(login_url='admin_login')
def user_change_password(request):
    """Change user password"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('user_profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'section': 'profile'
    }
    return render(request, 'accounts/user_change_password.html', context)