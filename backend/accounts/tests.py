import re
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth import SESSION_KEY
from django.conf import settings
from django.core import mail
from django.template.loader import get_template
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import AccountProfile


class SponsorDashboardTemplateTests(SimpleTestCase):
    def test_dashboard_template_renders(self):
        rendered = get_template('accounts/sponsor_dashboard.html').render({})

        self.assertIn('Sponsor Workspace', rendered)


class UnifiedLogoutTests(TestCase):
    def test_role_specific_logout_routes_return_to_unified_login(self):
        user_model = get_user_model()
        logout_routes = (
            ('admin', AccountProfile.ROLE_ADMIN, 'logout'),
            ('staff', AccountProfile.ROLE_STAFF, 'logout'),
            ('donor', AccountProfile.ROLE_DONOR, 'donor_logout'),
            ('sponsor', AccountProfile.ROLE_SPONSOR, 'sponsor_logout'),
        )

        for username, role, route_name in logout_routes:
            user = user_model.objects.create_user(
                username=username,
                password='test-password',
            )
            AccountProfile.objects.create(user=user, role=role)
            self.client.force_login(user)

            response = self.client.get(reverse(route_name))

            self.assertRedirects(response, reverse('login'))
            self.assertNotIn(SESSION_KEY, self.client.session)

        login_page = self.client.get(reverse('login'))
        self.assertContains(login_page, 'Login as:')
        self.assertContains(login_page, 'loginRoleSponsor')
        self.assertContains(login_page, 'loginRoleDonor')


class AccountNavigationTests(TestCase):
    def test_password_reset_link_opens_a_working_form(self):
        response = self.client.get(reverse('password_reset'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="email"')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetFlowTests(TestCase):
    def test_email_link_resets_the_password(self):
        user = get_user_model().objects.create_user(
            username='password-reset-user',
            email='password-reset@example.com',
            password='Old-password-123!',
        )

        response = self.client.post(reverse('password_reset'), {'email': user.email})

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])
        self.assertIn('Reset your KafalatCare password', mail.outbox[0].subject)
        reset_path_match = re.search(r'/accounts/reset/\S+', mail.outbox[0].body)
        self.assertIsNotNone(reset_path_match)
        response = self.client.get(urlsplit(reset_path_match.group(0)).path)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(response.request['PATH_INFO'], {
            'new_password1': 'New-strong-password-2026!',
            'new_password2': 'New-strong-password-2026!',
        }, follow=True)

        self.assertContains(response, 'Password updated')
        user.refresh_from_db()
        self.assertTrue(user.check_password('New-strong-password-2026!'))


class RememberMeTests(TestCase):
    login_routes = (
        (AccountProfile.ROLE_ADMIN, 'login'),
        (AccountProfile.ROLE_SPONSOR, 'sponsor_login'),
        (AccountProfile.ROLE_DONOR, 'donor_login'),
    )

    def _create_user(self, role, index):
        user = get_user_model().objects.create_user(
            username=f'remember-{role}-{index}',
            email=f'remember-{role}-{index}@example.com',
            password='Strong-test-password-2026!',
        )
        AccountProfile.objects.create(user=user, role=role)
        return user

    def test_checked_remember_me_keeps_session_persistent(self):
        for index, (role, route_name) in enumerate(self.login_routes):
            user = self._create_user(role, index)
            response = self.client.post(reverse(route_name), {
                'email': user.email,
                'password': 'Strong-test-password-2026!',
                'role': role,
                'remember': 'on',
            })

            self.assertEqual(response.status_code, 302)
            self.assertFalse(self.client.session.get_expire_at_browser_close())
            self.assertGreaterEqual(
                self.client.session.get_expiry_age(),
                settings.SESSION_COOKIE_AGE - 5,
            )
            self.client.logout()

    def test_unchecked_remember_me_expires_at_browser_close(self):
        for index, (role, route_name) in enumerate(self.login_routes):
            user = self._create_user(role, index)
            response = self.client.post(reverse(route_name), {
                'email': user.email,
                'password': 'Strong-test-password-2026!',
                'role': role,
            })

            self.assertEqual(response.status_code, 302)
            self.assertTrue(self.client.session.get_expire_at_browser_close())
            self.client.logout()
