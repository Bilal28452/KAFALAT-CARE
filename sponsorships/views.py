from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q

from accounts.views import is_admin_user, resolve_redirect
from accounts.dashboard import record_audit_log
from .models import Sponsorship
from .forms import SponsorshipForm
from children.models import Child


# ==================== SPONSORSHIP CRUD VIEWS ====================

@login_required(login_url='admin_login')
def sponsorship_list(request):
    """List all sponsorships with search and filter"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    sponsorships = Sponsorship.objects.select_related('child').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        sponsorships = sponsorships.filter(
            Q(sponsor_code__icontains=search_query) |
            Q(sponsor_name__icontains=search_query) |
            Q(cnic__icontains=search_query) |
            Q(child__full_name__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        sponsorships = sponsorships.filter(status=status_filter)
    
    record_audit_log(request, 'VIEW', 'Sponsorships', details='Viewed sponsorships list')
    
    context = {
        'sponsorships': sponsorships,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'sponsorships/sponsorship_list.html', context)


@login_required(login_url='admin_login')
def sponsorship_create(request):
    """Create a new sponsorship record"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        form = SponsorshipForm(request.POST)
        if form.is_valid():
            sponsorship = form.save(commit=False)
            # Link to logged-in user if they have an account
            if request.user.is_authenticated:
                sponsorship.sponsor = request.user
            sponsorship.save()
            
            # Update child's sponsor status
            if sponsorship.child:
                sponsorship.child.sponsor_status = 'sponsored'
                sponsorship.child.save()
            
            record_audit_log(
                request, 'CREATE', 'Sponsorships',
                record_id=sponsorship.sponsor_code,
                details=f'Created sponsorship: {sponsorship.sponsor_name} -> {sponsorship.child}'
            )
            messages.success(request, f'Sponsorship for {sponsorship.sponsor_name} created successfully.')
            return redirect(resolve_redirect(request, reverse('sponsorship_detail', kwargs={'pk': sponsorship.pk})))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SponsorshipForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'sponsorships/sponsorship_form.html', context)


@login_required(login_url='admin_login')
def sponsorship_detail(request, pk):
    """View detailed sponsorship information"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    sponsorship = get_object_or_404(Sponsorship.objects.select_related('child'), pk=pk)
    
    record_audit_log(
        request, 'VIEW', 'Sponsorships',
        record_id=sponsorship.sponsor_code,
        details=f'Viewed sponsorship details: {sponsorship.sponsor_name}'
    )
    
    context = {'sponsorship': sponsorship}
    return render(request, 'sponsorships/sponsorship_detail.html', context)


@login_required(login_url='admin_login')
def sponsorship_update(request, pk):
    """Update an existing sponsorship record"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    sponsorship = get_object_or_404(Sponsorship, pk=pk)
    old_child = sponsorship.child
    
    if request.method == 'POST':
        form = SponsorshipForm(request.POST, instance=sponsorship)
        if form.is_valid():
            sponsorship = form.save()
            
            # Update child sponsor status if child changed
            if old_child != sponsorship.child:
                # Mark old child as available
                if old_child:
                    old_child.sponsor_status = 'available'
                    old_child.save()
                # Mark new child as sponsored
                if sponsorship.child:
                    sponsorship.child.sponsor_status = 'sponsored'
                    sponsorship.child.save()
            
            record_audit_log(
                request, 'UPDATE', 'Sponsorships',
                record_id=sponsorship.sponsor_code,
                details=f'Updated sponsorship: {sponsorship.sponsor_name}'
            )
            messages.success(request, f'Sponsorship for {sponsorship.sponsor_name} updated successfully.')
            return redirect(resolve_redirect(request, reverse('sponsorship_detail', kwargs={'pk': sponsorship.pk})))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SponsorshipForm(instance=sponsorship)
    
    context = {'form': form, 'action': 'Update', 'sponsorship': sponsorship}
    return render(request, 'sponsorships/sponsorship_form.html', context)


@login_required(login_url='admin_login')
def sponsorship_delete(request, pk):
    """Delete a sponsorship record"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    sponsorship = get_object_or_404(Sponsorship, pk=pk)
    
    if request.method == 'POST':
        sponsor_name = sponsorship.sponsor_name
        sponsor_code = sponsorship.sponsor_code
        child = sponsorship.child
        
        # Mark child as available again
        if child:
            child.sponsor_status = 'available'
            child.save()
        
        sponsorship.delete()
        record_audit_log(
            request, 'DELETE', 'Sponsorships',
            record_id=sponsor_code,
            details=f'Deleted sponsorship: {sponsor_name}'
        )
        messages.success(request, f'Sponsorship for {sponsor_name} deleted successfully.')
        return redirect(resolve_redirect(request, reverse('sponsorship_list')))
    
    context = {'sponsorship': sponsorship}
    return render(request, 'sponsorships/sponsorship_confirm_delete.html', context)


def calculate_sponsorship_match(child):
    score = 50
    if child.health_status in ('under_care', 'medical_care', 'observation'):
        score += 18
    elif child.health_status == 'healthy':
        score += 10
    if hasattr(child, 'education_record'):
        score += 12
    if getattr(child, 'education_level', ''):
        score += 8
    if child.photo:
        score += 4
    if child.date_of_birth:
        score += 4
    return min(score, 98)


@login_required(login_url='admin_login')
def sponsorship_approve(request, pk):
    if not is_admin_user(request.user):
        return redirect('index')
    sponsorship = get_object_or_404(Sponsorship, pk=pk)
    if request.method == 'POST' and sponsorship.status == 'pending':
        available = Child.objects.filter(sponsor_status='available')
        ranked = sorted(available, key=lambda child: calculate_sponsorship_match(child), reverse=True)
        if not ranked:
            messages.error(request, 'No available child is available for matching.')
            return redirect('sponsorship_detail', pk=sponsorship.pk)
        child = ranked[0]
        sponsorship.child = child
        sponsorship.status = 'active'
        sponsorship.ai_match_score = calculate_sponsorship_match(child)
        sponsorship.admin_notes = request.POST.get('admin_notes', '').strip()
        sponsorship.save()
        child.sponsor_status = 'sponsored'
        child.save(update_fields=['sponsor_status'])
        record_audit_log(request, 'UPDATE', 'Sponsorships', record_id=sponsorship.sponsor_code, details=f'AI matched and approved {child.full_name}')
        messages.success(request, f'Request approved. AI matched {child.full_name} to this sponsor.')
    return redirect('sponsorship_detail', pk=sponsorship.pk)


@login_required(login_url='admin_login')
def sponsorship_reject(request, pk):
    if not is_admin_user(request.user):
        return redirect('index')
    sponsorship = get_object_or_404(Sponsorship, pk=pk)
    if request.method == 'POST' and sponsorship.status == 'pending':
        sponsorship.status = 'rejected'
        sponsorship.admin_notes = request.POST.get('admin_notes', '').strip()
        sponsorship.save(update_fields=['status', 'admin_notes'])
        record_audit_log(request, 'UPDATE', 'Sponsorships', record_id=sponsorship.sponsor_code, details='Rejected sponsor request')
        messages.success(request, 'Sponsorship request rejected.')
    return redirect('sponsorship_detail', pk=sponsorship.pk)
