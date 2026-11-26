from accounts.models import AccountProfile
from payments.models import Payment

from .models import Notification, SponsorshipMessage


def unread_messages_for(user):
    profile = getattr(user, 'account_profile', None)
    if not profile:
        return SponsorshipMessage.objects.none()

    messages = SponsorshipMessage.objects.filter(
        conversation__sponsorship__status='active',
        read_at__isnull=True,
    ).exclude(sender=user)

    if profile.role == AccountProfile.ROLE_SPONSOR:
        return messages.filter(
            conversation__sponsorship__sponsor=user,
            conversation__sponsorship__payment_transactions__status=Payment.STATUS_PAID,
        ).distinct()
    if profile.role == AccountProfile.ROLE_STAFF:
        return messages.filter(
            conversation__staff__user=user,
            conversation__staff__employment_status='active',
        )
    return SponsorshipMessage.objects.none()


def communication_badges(user):
    if not user.is_authenticated:
        return {
            'unread_notification_count': 0,
            'unread_message_count': 0,
        }

    return {
        'unread_notification_count': Notification.objects.filter(
            recipient=user,
            read_at__isnull=True,
        ).count(),
        'unread_message_count': unread_messages_for(user).count(),
    }


def communication_activity(user):
    notifications = Notification.objects.filter(
        recipient=user,
        read_at__isnull=True,
    )[:5]
    messages = unread_messages_for(user).select_related(
        'sender',
        'conversation__sponsorship__child',
        'conversation__staff__user',
    ).order_by('-created_at')[:5]
    return {
        'dashboard_notifications': notifications,
        'dashboard_messages': messages,
    }
