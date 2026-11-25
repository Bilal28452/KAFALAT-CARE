from django.dispatch import receiver

from allauth.account.signals import user_logged_in, user_signed_up

from .models import AccountProfile


@receiver(user_signed_up)
def create_account_profile_for_social_user(request, user, sociallogin=None, **kwargs):
    AccountProfile.objects.get_or_create(
        user=user,
        defaults={
            'role': AccountProfile.ROLE_DONOR,
        },
    )


@receiver(user_logged_in)
def ensure_account_profile_exists(request, user, **kwargs):
    if not hasattr(user, 'account_profile'):
        AccountProfile.objects.create(user=user, role=AccountProfile.ROLE_DONOR)
