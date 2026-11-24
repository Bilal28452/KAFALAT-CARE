from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q

from accounts.views import is_admin_user, resolve_redirect
from accounts.dashboard import record_audit_log
from .models import Donation
from .forms import DonationForm


# ==================== DONATION CRUD VIEWS ====================

@login_required(login_url='admin_login')
def donation_list(request):
    """List all donations with search and filter"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    donations = Donation.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        donations = donations.filter(
            Q(donor_name__icontains=search_query) |
            Q(transaction_id__icontains=search_query) |
            Q(receipt_number__icontains=search_query)
        )
    
    # Filter by donation type
    type_filter = request.GET.get('donation_type', '')
    if type_filter:
        donations = donations.filter(donation_type=type_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        donations = donations.filter(status=status_filter)
    
    # Filter by donor type
    donor_type_filter = request.GET.get('donor_type', '')
    if donor_type_filter:
        donations = donations.filter(donor_type=donor_type_filter)
    
    record_audit_log(request, 'VIEW', 'Donations', details='Viewed donations list')
    
    context = {
        'donations': donations,
        'search_query': search_query,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'donor_type_filter': donor_type_filter,
    }
    return render(request, 'donations/donation_list.html', context)


@login_required(login_url='admin_login')
def donation_create(request):
    """Create a new donation record"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            # Link to logged-in user if they have an account
            if request.user.is_authenticated:
                donation.donor = request.user
            donation.save()
            
            record_audit_log(
                request, 'CREATE', 'Donations',
                record_id=str(donation.pk),
                details=f'Created donation record: {donation.donor_name} - PKR {donation.amount}'
            )
            messages.success(request, f'Donation from {donation.donor_name} recorded successfully.')
            return redirect(resolve_redirect(request, reverse('donation_detail', kwargs={'pk': donation.pk})))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DonationForm()
    
    context = {'form': form, 'action': 'Create'}
    return render(request, 'donations/donation_form.html', context)


@login_required(login_url='admin_login')
def donation_detail(request, pk):
    """View detailed donation information"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    donation = get_object_or_404(Donation, pk=pk)
    
    record_audit_log(
        request, 'VIEW', 'Donations',
        record_id=str(donation.pk),
        details=f'Viewed donation details: {donation.donor_name}'
    )
    
    context = {'donation': donation}
    return render(request, 'donations/donation_detail.html', context)


@login_required(login_url='admin_login')
def donation_update(request, pk):
    """Update an existing donation record"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    donation = get_object_or_404(Donation, pk=pk)
    
    if request.method == 'POST':
        form = DonationForm(request.POST, instance=donation)
        if form.is_valid():
            donation = form.save()
            record_audit_log(
                request, 'UPDATE', 'Donations',
                record_id=str(donation.pk),
                details=f'Updated donation record: {donation.donor_name}'
            )
            messages.success(request, f'Donation from {donation.donor_name} updated successfully.')
            return redirect(resolve_redirect(request, reverse('donation_detail', kwargs={'pk': donation.pk})))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DonationForm(instance=donation)
    
    context = {'form': form, 'action': 'Update', 'donation': donation}
    return render(request, 'donations/donation_form.html', context)


@login_required(login_url='admin_login')
def donation_delete(request, pk):
    """Delete a donation record"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    donation = get_object_or_404(Donation, pk=pk)
    
    if request.method == 'POST':
        donor_name = donation.donor_name
        amount = donation.amount
        record_id = str(donation.pk)
        donation.delete()
        record_audit_log(
            request, 'DELETE', 'Donations',
            record_id=record_id,
            details=f'Deleted donation record: {donor_name} - PKR {amount}'
        )
        messages.success(request, f'Donation from {donor_name} deleted successfully.')
        return redirect(resolve_redirect(request, reverse('donation_list')))
    
    context = {'donation': donation}
    return render(request, 'donations/donation_confirm_delete.html', context)
