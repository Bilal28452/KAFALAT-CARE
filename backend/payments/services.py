from decimal import Decimal

from django.db import IntegrityError, transaction

from .models import Payment


def get_or_create_donation_payment(donation):
    if donation.status == 'completed' or Payment.objects.filter(
        donation=donation,
        status=Payment.STATUS_PAID,
    ).exists():
        raise ValueError('This donation has already been paid.')
    if donation.amount < Decimal('100.00'):
        raise ValueError('The minimum online donation is PKR 100.')
    with transaction.atomic():
        donation.status = 'pending'
        donation.payment_method = 'Safepay'
        donation.save(update_fields=['status', 'payment_method'])
        payment, _ = Payment.objects.get_or_create(
            donation=donation,
            status=Payment.STATUS_PENDING,
            defaults={
                'initiated_by': donation.donor,
                'purpose': Payment.PURPOSE_DONATION,
                'amount': donation.amount,
                'currency': 'PKR',
            },
        )
        if payment.amount != donation.amount:
            raise ValueError('The pending checkout amount differs from this donation; contact support.')
    return payment


def get_or_create_sponsorship_payment(sponsorship):
    if sponsorship.status != 'active':
        raise ValueError('Only an approved, active sponsorship can be paid.')
    amount = Decimal(sponsorship.monthly_amount)
    if amount <= 0:
        raise ValueError('The sponsorship amount must be greater than zero.')
    try:
        with transaction.atomic():
            payment, _ = Payment.objects.get_or_create(
                sponsorship=sponsorship,
                status=Payment.STATUS_PENDING,
                defaults={
                    'initiated_by': sponsorship.sponsor,
                    'purpose': Payment.PURPOSE_SPONSORSHIP,
                    'amount': amount,
                    'currency': 'PKR',
                },
            )
            if payment.amount != amount:
                raise ValueError('The pending checkout amount differs from this sponsorship; contact support.')
    except IntegrityError:
        payment = Payment.objects.get(
            sponsorship=sponsorship,
            status=Payment.STATUS_PENDING,
        )
    return payment


def has_verified_sponsorship_payment(sponsorship):
    return Payment.objects.filter(
        sponsorship_id=sponsorship.pk,
        status=Payment.STATUS_PAID,
    ).exists()
