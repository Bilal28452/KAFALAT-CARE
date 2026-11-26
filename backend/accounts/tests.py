from django.contrib.auth import get_user_model
from django.contrib.auth import SESSION_KEY
from django.template.loader import get_template
from django.test import SimpleTestCase, TestCase
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
