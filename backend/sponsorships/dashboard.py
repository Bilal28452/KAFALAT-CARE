from django.urls import reverse

from core.dashboard import badge, format_money

from .models import Sponsorship


def sponsorships_section():
    rows = []
    for sponsorship in Sponsorship.objects.select_related('child')[:50]:
        rows.append({
            'view_url': reverse('sponsorship_detail', args=[sponsorship.pk]),
            'edit_url': reverse('sponsorship_update', args=[sponsorship.pk]),
            'delete_url': reverse('sponsorship_delete', args=[sponsorship.pk]),
            'delete_label': f'{sponsorship.sponsor_name} sponsorship',
            'cells': [
                sponsorship.sponsor_name,
                sponsorship.sponsor_code,
                sponsorship.cnic,
                sponsorship.phone,
                sponsorship.email,
                sponsorship.child.full_name if sponsorship.child else 'Unassigned',
                format_money(sponsorship.monthly_amount),
                sponsorship.start_date,
                sponsorship.payment_method,
                sponsorship.last_payment_date or '',
                sponsorship.next_payment_date or '',
                badge(sponsorship.get_status_display(), 'success' if sponsorship.status == 'active' else 'warning'),
                f'{sponsorship.ai_match_score}%',
            ],
        })

    return {
        'id': 'sponsorships',
        'title': 'Sponsorship Management',
        'icon': 'bi bi-heart',
        'action_label': 'Match Sponsor',
        'action_url': reverse('sponsorship_create'),
        'empty_message': 'No sponsorships found. Add a sponsorship from the Sponsorships module.',
        'headings': ['Sponsor Name', 'Sponsor ID', 'CNIC', 'Phone', 'Email', 'Sponsored Child', 'Monthly Amount', 'Start Date', 'Payment Method', 'Last Payment', 'Next Payment', 'Status', 'AI Match Score'],
        'rows': rows,
    }


def stats():
    return {'active_sponsors': Sponsorship.objects.filter(status='active').count()}
