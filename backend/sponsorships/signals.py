from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from children.models import Attendance, EducationRecord, EducationResult, HealthRecord
from meals.models import MealRecord
from payments.models import Payment

from .models import Sponsorship
from .notifications import notify_users


UPDATE_LABELS = {
    HealthRecord: 'health',
    EducationRecord: 'education',
    EducationResult: 'education',
    Attendance: 'attendance',
    MealRecord: 'meal',
}


@receiver(post_save, sender=HealthRecord)
@receiver(post_save, sender=EducationRecord)
@receiver(post_save, sender=EducationResult)
@receiver(post_save, sender=Attendance)
@receiver(post_save, sender=MealRecord)
def notify_sponsors_of_new_child_record(sender, instance, created, **kwargs):
    if not created:
        return

    sponsorships = Sponsorship.objects.filter(
        child_id=instance.child_id,
        status='active',
        sponsor__isnull=False,
        payment_transactions__status=Payment.STATUS_PAID,
    ).select_related('sponsor').distinct()
    recipients = [sponsorship.sponsor for sponsorship in sponsorships]
    if not recipients:
        return

    label = UPDATE_LABELS[sender]
    notify_users(
        recipients,
        f'New {label} update available',
        f"A new {label} record is available in your sponsored child's private progress page.",
        reverse('sponsor_child_detail', kwargs={'pk': instance.child_id}),
    )
