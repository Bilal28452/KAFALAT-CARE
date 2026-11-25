from django.template.loader import get_template
from django.test import SimpleTestCase


class SponsorDashboardTemplateTests(SimpleTestCase):
    def test_dashboard_template_renders(self):
        rendered = get_template('accounts/sponsor_dashboard.html').render({})

        self.assertIn('Sponsor Workspace', rendered)
