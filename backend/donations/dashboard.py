from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from core.dashboard import badge, format_money

from .models import Donation


def donations_section():
    rows = []
    for donation in Donation.objects.all()[:50]:
        rows.append({
            'view_url': reverse('donation_detail', args=[donation.pk]),
            'edit_url': reverse('donation_update', args=[donation.pk]),
            'delete_url': reverse('donation_delete', args=[donation.pk]),
            'delete_label': f'{donation.donor_name} donation of PKR {donation.amount:,.2f}',
            'cells': [
                donation.donor_name,
                donation.get_donor_type_display(),
                format_money(donation.amount),
                donation.get_donation_type_display(),
                donation.payment_method,
                donation.transaction_id,
                donation.donated_at,
                donation.allocated_to,
                donation.receipt_number,
                badge('Issued', 'info') if donation.tax_certificate_issued else badge('Pending', 'warning'),
                badge(donation.get_status_display(), 'success' if donation.status == 'completed' else 'warning'),
            ],
        })

    return {
        'id': 'donations',
        'title': 'Donations Management',
        'icon': 'bi bi-gift',
        'action_label': 'Record Donation',
        'action_url': reverse('donation_create'),
        'empty_message': 'No donations found. Add a donation from the Donations module.',
        'headings': ['Donor Name', 'Donor Type', 'Amount', 'Donation Type', 'Payment Method', 'Transaction ID', 'Date', 'Allocated To', 'Receipt #', 'Tax Certificate', 'Status'],
        'rows': rows,
    }


def stats():
    today = timezone.localdate()
    total = Donation.objects.filter(
        status='completed',
        donated_at__year=today.year,
        donated_at__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or 0
    return {'monthly_donations': total}
