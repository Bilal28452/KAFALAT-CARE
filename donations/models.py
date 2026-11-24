from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Donation(models.Model):
    DONOR_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('corporate', 'Corporate'),
        ('organization', 'Organization'),
    ]
    DONATION_TYPE_CHOICES = [
        ('one_time', 'One-time'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('zakat', 'Zakat'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    donor_name = models.CharField(max_length=140)
    donor_type = models.CharField(max_length=20, choices=DONOR_TYPE_CHOICES, default='individual')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPE_CHOICES, default='one_time')
    payment_method = models.CharField(max_length=60, blank=True)
    transaction_id = models.CharField(max_length=80, blank=True)
    donated_at = models.DateField(default=timezone.localdate)
    allocated_to = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(max_length=40, blank=True)
    tax_certificate_issued = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-donated_at', '-created_at']

    def __str__(self):
        return f'{self.donor_name} - {self.amount}'
