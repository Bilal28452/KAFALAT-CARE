from django.db.models import Sum
from django.utils import timezone

from .models import Payment


def stats():
    today = timezone.localdate()
    total = Payment.objects.filter(
        purpose=Payment.PURPOSE_SPONSORSHIP,
        status=Payment.STATUS_PAID,
        paid_at__year=today.year,
        paid_at__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or 0
    return {'monthly_sponsorship_payments': total}
