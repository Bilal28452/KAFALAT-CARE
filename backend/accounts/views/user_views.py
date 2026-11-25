from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator

from .auth_views import is_admin_user
from ..models import AccountProfile

User = get_user_model()


def is_admin_user(user):
    if user.is_superuser:
        return True
    return hasattr(user, 'account_profile') and user.account_profile.role == AccountProfile.ROLE_ADMIN


@login_required(login_url='admin_login')
def user_list(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    users = User.objects.select_related('account_profile').all().order_by('-date_joined')
    
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(account_profile__phone__icontains=search_query) |
            Q(account_profile__cnic__icontains=search_query)
        )
    
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(account_profile__role=role_filter)
    
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    roles = AccountProfile.objects.values_list('role', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': roles,
        'total_users': users.count(),
        'section': 'users'
    }
    return render(request, 'accounts/users/user_list.html', context)


@login_required(login_url='admin_login')
def user_detail(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    user = get_object_or_404(User.objects.select_related('account_profile'), pk=pk)
    context = {'user': user, 'section': 'users'}
    return render(request, 'accounts/users/user_detail.html', context)


@login_required(login_url='admin_login')
def user_create(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        cnic = request.POST.get('cnic')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active
            )
            AccountProfile.objects.create(
                user=user,
                phone=phone,
                cnic=cnic,
                role=role
            )
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('user_detail', pk=user.pk)
    
    context = {
        'section': 'users',
        'roles': AccountProfile.ROLE_CHOICES,
        'action': 'Create'
    }
    return render(request, 'accounts/users/user_form.html', context)


@login_required(login_url='admin_login')
def user_update(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    user = get_object_or_404(User.objects.select_related('account_profile'), pk=pk)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        cnic = request.POST.get('cnic')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = is_active
        user.save()
        
        if hasattr(user, 'account_profile'):
            user.account_profile.phone = phone
            user.account_profile.cnic = cnic
            user.account_profile.role = role
            user.account_profile.save()
        else:
            AccountProfile.objects.create(user=user, phone=phone, cnic=cnic, role=role)
        
        messages.success(request, f'User {user.username} updated successfully.')
        return redirect('user_detail', pk=user.pk)
    
    context = {
        'user': user,
        'section': 'users',
        'roles': AccountProfile.ROLE_CHOICES,
        'action': 'Update'
    }
    return render(request, 'accounts/users/user_form.html', context)


@login_required(login_url='admin_login')
def user_delete(request, pk):
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully.')
        return redirect('user_list')
    
    context = {'user': user, 'section': 'users'}
    return render(request, 'accounts/users/user_confirm_delete.html', context)