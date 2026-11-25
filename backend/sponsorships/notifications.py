import logging
import smtplib

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from .models import Notification


logger = logging.getLogger(__name__)


def _send_notification_email(recipient_id, recipient_email, title, body):
    try:
        send_mail(
            subject=title,
            message=f'{body}\n\nSign in to KafalatCare to view the update.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
    except (OSError, smtplib.SMTPException):
        logger.exception('Could not send sponsorship notification email to user %s.', recipient_id)


def notify_users(recipients, title, body, url=''):
    unique_recipients = {user.pk: user for user in recipients if user and user.pk}
    for recipient in unique_recipients.values():
        Notification.objects.create(
            recipient=recipient,
            title=title,
            body=body,
            url=url,
        )
        if not recipient.email:
            continue
        transaction.on_commit(
            lambda recipient_id=recipient.pk, recipient_email=recipient.email:
                _send_notification_email(recipient_id, recipient_email, title, body)
        )
