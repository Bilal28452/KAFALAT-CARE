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
    agreement_accepted_at = models.DateTimeField(null=True, blank=True)
    agreement_version = models.CharField(max_length=30, blank=True)
    minimum_commitment_end_date = models.DateField(null=True, blank=True)
    ended_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        constraints = [
            models.UniqueConstraint(
                fields=('sponsor',),
                condition=(
                    models.Q(sponsor__isnull=False)
                    & models.Q(status__in=['pending', 'active', 'paused'])
                ),
                name='one_current_sponsorship_per_sponsor',
            ),
        ]

    def __str__(self):
        return f'{self.sponsor_name} -> {self.child or "Unassigned"}'


class SponsorshipConversation(models.Model):
    sponsorship = models.ForeignKey(Sponsorship, on_delete=models.CASCADE, related_name='conversations')
    staff = models.ForeignKey(
        'staff_management.StaffMember',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sponsorship_conversations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('sponsorship', 'staff'), name='unique_sponsorship_staff_conversation'),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.sponsorship.sponsor_name} - {self.staff or "Unassigned staff"}'


class SponsorshipMessage(models.Model):
    conversation = models.ForeignKey(
        SponsorshipConversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Message in conversation {self.conversation_id} by {self.sender}'


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sponsorship_notifications',
    )
    title = models.CharField(max_length=160)
    body = models.CharField(max_length=300)
    url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} for {self.recipient}'
