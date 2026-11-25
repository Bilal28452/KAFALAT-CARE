from datetime import date
from unittest.mock import patch

import requests
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Child, HealthRecord


class HealthPatternIntegrationTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_superuser(
            username='health-admin',
            email='health-admin@example.com',
            password='test-password',
        )
        self.client.force_login(user)
        self.child = Child.objects.create(child_id='CH001', full_name='Test Child')
        HealthRecord.objects.create(
            child=self.child,
            last_checkup=date(2026, 3, 10),
            weight='30 kg',
            temperature_c='38.4',
            symptoms='cough, sore throat',
        )

    def test_health_record_detail_renders_valid_back_link(self):
        record = self.child.health_records.get()

        response = self.client.get(reverse('health_record_detail', args=[record.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('dashboard') + '?section=health')
        self.assertContains(response, '38.4 °C')

    @override_settings(AI_SERVICE_URL='http://ai.test', AI_SERVICE_API_KEY='test-key')
    @patch('children.views.health_views.requests.post')
    def test_analysis_sends_saved_health_data_and_shows_alerts(self, post):
        post.return_value.json.return_value = {
            'alerts': [{
                'code': 'FEVER',
                'severity': 'medium',
                'message': 'Fever recorded; staff review is recommended.',
            }],
            'note': 'AI Suggested. Staff make the final decision.',
        }

        response = self.client.post(
            reverse('health_pattern_analyze', args=[self.child.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fever recorded; staff review is recommended.')
        post.assert_called_once()
        self.assertEqual(post.call_args.args[0], 'http://ai.test/health-pattern')
        self.assertEqual(post.call_args.kwargs['headers'], {'X-API-Key': 'test-key'})
        self.assertEqual(post.call_args.kwargs['json'], {
            'child_id': 'CH001',
            'records': [{
                'date': '2026-03-10',
                'weight_kg': 30.0,
                'temperature_c': 38.4,
                'symptoms': ['cough', 'sore throat'],
            }],
        })

    @patch('children.views.health_views.requests.post', side_effect=requests.ConnectionError)
    def test_service_unavailable_is_reported_to_staff(self, post):
        response = self.client.post(
            reverse('health_pattern_analyze', args=[self.child.pk]),
            follow=True,
        )

        self.assertContains(response, 'Could not reach the AI service.')
