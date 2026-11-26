import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from donations.models import Donation
from sponsorships.models import Sponsorship


class Payment(models.Model):
    PURPOSE_DONATION = 'donation'
    PURPOSE_SPONSORSHIP = 'sponsorship'
    PURPOSE_CHOICES = [
        (PURPOSE_DONATION, 'Donation'),
        (PURPOSE_SPONSORSHIP, 'Sponsorship'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
    ]

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_transactions',
    )
    donation = models.ForeignKey(
        Donation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='payment_transactions',
    )
    sponsorship = models.ForeignKey(
        Sponsorship,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='payment_transactions',
    )
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='PKR')
    tracker_token = models.CharField(max_length=150, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        purpose='donation',
                        donation__isnull=False,
                        sponsorship__isnull=True,
                    )
                    | Q(
                        purpose='sponsorship',
                        donation__isnull=True,
                        sponsorship__isnull=False,
                    )
                ),
                name='payment_has_one_matching_target',
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name='payment_amount_is_positive',
            ),
            models.UniqueConstraint(
                fields=('donation',),
                condition=Q(donation__isnull=False, status='pending'),
                name='one_pending_payment_per_donation',
            ),
            models.UniqueConstraint(
                fields=('sponsorship',),
                condition=Q(sponsorship__isnull=False, status='pending'),
                name='one_pending_payment_per_sponsorship',
            ),
        ]

    def __str__(self):
        return f'{self.get_purpose_display()} {self.amount} {self.currency} ({self.status})'


class PaymentWebhookEvent(models.Model):
    event_token = models.CharField(max_length=150, unique=True)
    event_type = models.CharField(max_length=100)
    received_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-received_at']

    def __str__(self):
        return f'{self.event_type} ({self.event_token})'
