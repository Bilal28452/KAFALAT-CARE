import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Create or update SocialApp entries from environment variables.'

    def handle(self, *args, **options):
        try:
            from allauth.socialaccount.models import SocialApp
            from django.contrib.sites.models import Site
        except Exception as e:
            self.stderr.write('django-allauth not available or models import failed: %s' % e)
            return

        site_id = getattr(settings, 'SITE_ID', 1)
        try:
            site = Site.objects.get(pk=site_id)
        except Site.DoesNotExist:
            self.stderr.write(f'Site with id={site_id} does not exist. Create a Site first.')
            return

        providers = [
            ('google', 'Google', 'SOCIAL_GOOGLE_CLIENT_ID', 'SOCIAL_GOOGLE_SECRET'),
            ('github', 'GitHub', 'SOCIAL_GITHUB_CLIENT_ID', 'SOCIAL_GITHUB_SECRET'),
            ('microsoft', 'Microsoft', 'SOCIAL_MICROSOFT_CLIENT_ID', 'SOCIAL_MICROSOFT_SECRET'),
        ]

        created_any = False
        for provider, name, env_id, env_secret in providers:
            client_id = os.getenv(env_id)
            secret = os.getenv(env_secret)
            if not client_id or not secret:
                self.stdout.write(self.style.WARNING(
                    f'Skipping {provider}: set {env_id} and {env_secret} to create this SocialApp.'
                ))
                continue

            app, created = SocialApp.objects.update_or_create(
                provider=provider,
                defaults={
                    'name': name,
                    'client_id': client_id,
                    'secret': secret,
                }
            )
            app.sites.add(site)
            created_any = True
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} SocialApp for {provider} (id={app.pk}).'))

        if not created_any:
            self.stdout.write(self.style.NOTICE('No SocialApp created. Provide env vars for at least one provider.'))
