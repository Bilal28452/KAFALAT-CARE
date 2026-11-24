from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from children.models import Child


class Sponsorship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Admin Approval'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('ended', 'Ended'),
        ('rejected', 'Rejected'),
    ]

    sponsor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    sponsor_code = models.CharField(max_length=30, unique=True)
    sponsor_name = models.CharField(max_length=140)
    cnic = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    child = models.ForeignKey(Child, on_delete=models.SET_NULL, null=True, blank=True, related_name='sponsorships')
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    start_date = models.DateField(default=timezone.localdate)
    payment_method = models.CharField(max_length=60, blank=True)
    last_payment_date = models.DateField(null=True, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    ai_match_score = models.PositiveSmallIntegerField(default=0)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.sponsor_name} -> {self.child or "Unassigned"}'
