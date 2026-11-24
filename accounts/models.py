from django.conf import settings
from django.db import models


class AccountProfile(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_DONOR = 'donor'
    ROLE_SPONSOR = 'sponsor'
    ROLE_STAFF = 'staff'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_DONOR, 'Donor'),
        (ROLE_SPONSOR, 'Sponsor'),
        (ROLE_STAFF, 'Staff'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='account_profile',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ADMIN)
    phone = models.CharField(max_length=30, blank=True)
    cnic = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email or self.user.username} ({self.get_role_display()})'


class AuditLog(models.Model):
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    user_role = models.CharField(max_length=40, blank=True)
    action = models.CharField(max_length=80)
    module = models.CharField(max_length=80)
    record_id = models.CharField(max_length=80, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at:%Y-%m-%d %H:%M} - {self.action} - {self.module}'
