import hashlib
import hmac
import json
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import AccountProfile
from children.models import Child, EducationRecord
from donations.models import Donation
from sponsorships.models import Sponsorship

from .dashboard import stats
from .gateway import create_checkout_url
from .models import Payment, PaymentWebhookEvent


@override_settings(
    SAFEPAY_ENV='sandbox',
    SAFEPAY_API_KEY='test-public-key',
    SAFEPAY_SECRET_KEY='test-private-key',
    SAFEPAY_WEBHOOK_SECRET='test-webhook-secret',
    SAFEPAY_TIMEOUT=5,
    SITE_URL='https://kafalatcare.test',
)
class SafepayPaymentTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.donor = user_model.objects.create_user(
            username='donor',
            email='donor@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=self.donor, role=AccountProfile.ROLE_DONOR)
        self.sponsor = user_model.objects.create_user(
            username='sponsor',
            email='sponsor@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=self.sponsor, role=AccountProfile.ROLE_SPONSOR)
        self.child = Child.objects.create(
            child_id='PAY-100',
            full_name='Payment Child',
            education_level='Primary',
        )

    def create_donation(self, status='pending'):
        return Donation.objects.create(
            donor=self.donor,
            donor_name='Donor',
            amount=Decimal('500.00'),
            status=status,
        )

    def create_sponsorship(self, status='active'):
        return Sponsorship.objects.create(
            sponsor=self.sponsor,
            sponsor_code=f'SP-PAY-{Sponsorship.objects.count() + 1:03d}',
            sponsor_name='Sponsor',
            monthly_amount=Decimal('7500.00'),
            start_date=date(2026, 1, 1),
            status=status,
            child=self.child,
        )

    @staticmethod
    def signed_webhook(payload):
        body = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signature = hmac.new(
            b'test-webhook-secret',
            body,
            hashlib.sha512,
        ).hexdigest()
        return body, signature

    def post_webhook(self, payload):
        body, signature = self.signed_webhook(payload)
        return self.client.post(
            reverse('safepay_webhook'),
            data=body,
            content_type='application/json',
            HTTP_X_SFPY_SIGNATURE=signature,
        )

    def test_gateway_creates_tracker_and_hosted_checkout_url(self):
        payment = Payment.objects.create(
            initiated_by=self.donor,
            donation=self.create_donation(),
            purpose=Payment.PURPOSE_DONATION,
            amount=Decimal('125.50'),
        )
        tracker_response = Mock()
        tracker_response.json.return_value = {
            'data': {'tracker': {'token': 'track_test_123'}},
        }
        auth_response = Mock()
        auth_response.json.return_value = {'data': 'temporary-auth-token'}

        with patch(
            'payments.gateway.requests.post',
            side_effect=[tracker_response, auth_response],
        ) as post:
            checkout_url = create_checkout_url(
                payment,
                'https://kafalatcare.test/payments/return/',
                'https://kafalatcare.test/payments/cancel/',
            )

        payment.refresh_from_db()
        self.assertEqual(payment.tracker_token, 'track_test_123')
        self.assertEqual(post.call_args_list[0].kwargs['json']['amount'], 12550)
        self.assertEqual(
            post.call_args_list[0].kwargs['json']['metadata'],
            {'order_id': str(payment.reference)},
        )
        self.assertEqual(
            post.call_args_list[0].kwargs['headers']['X-SFPY-MERCHANT-SECRET'],
            'test-private-key',
        )
        self.assertEqual(urlparse(checkout_url).netloc, 'sandbox.api.getsafepay.com')
        query = parse_qs(urlparse(checkout_url).query)
        self.assertEqual(query['tracker'], ['track_test_123'])
        self.assertEqual(query['tbt'], ['temporary-auth-token'])

    def test_donor_submission_creates_pending_payment_and_redirects_to_checkout(self):
        self.client.force_login(self.donor)
        with patch(
            'payments.views.create_checkout_url',
            return_value='https://sandbox.api.getsafepay.com/embedded/?checkout=1',
        ):
            response = self.client.post(reverse('donor_donation_create'), {
                'donor_type': 'individual',
                'amount': '250.00',
                'donation_type': 'one_time',
                'allocated_to': 'Education',
            })

        donation = Donation.objects.get(donor=self.donor)
        payment = Payment.objects.get(donation=donation)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://sandbox.api.getsafepay.com/embedded/?checkout=1')
        self.assertEqual(donation.status, 'pending')
        self.assertEqual(payment.status, Payment.STATUS_PENDING)
        self.assertEqual(payment.amount, Decimal('250.00'))

    def test_online_donation_enforces_minimum_amount(self):
        self.client.force_login(self.donor)

        response = self.client.post(reverse('donor_donation_create'), {
            'donor_type': 'individual',
            'amount': '99.99',
            'donation_type': 'one_time',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'minimum online donation is PKR 100')
        self.assertFalse(Donation.objects.filter(donor=self.donor).exists())
        self.assertFalse(Payment.objects.exists())

    def test_donor_cannot_pay_another_users_donation(self):
        other_user = get_user_model().objects.create_user(
            username='other-donor',
            email='other@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=other_user, role=AccountProfile.ROLE_DONOR)
        donation = self.create_donation()
        self.client.force_login(other_user)

        response = self.client.post(reverse('donation_checkout', args=[donation.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Payment.objects.filter(donation=donation).exists())

    def test_sponsor_payment_uses_database_monthly_amount_and_requires_approval(self):
        sponsorship = self.create_sponsorship()
        self.client.force_login(self.sponsor)
        with patch(
            'payments.views.create_checkout_url',
            return_value='https://sandbox.api.getsafepay.com/embedded/?checkout=1',
        ):
            response = self.client.post(reverse('sponsorship_checkout', args=[sponsorship.pk]))

        payment = Payment.objects.get(sponsorship=sponsorship)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(payment.amount, Decimal('7500.00'))
        self.assertEqual(payment.status, Payment.STATUS_PENDING)

        sponsorship.status = 'ended'
        sponsorship.save(update_fields=['status'])
        pending = self.create_sponsorship(status='pending')
        response = self.client.post(reverse('sponsorship_checkout', args=[pending.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Payment.objects.filter(sponsorship=pending).exists())

    def test_valid_webhook_marks_donation_paid_and_duplicate_is_idempotent(self):
        donation = self.create_donation()
        payment = Payment.objects.create(
            initiated_by=self.donor,
            donation=donation,
            purpose=Payment.PURPOSE_DONATION,
            amount=Decimal('500.00'),
            tracker_token='track_donation_1',
        )
        payload = {
            'token': 'evt_donation_1',
            'type': 'payment.succeeded',
            'data': {
                'tracker': payment.tracker_token,
                'state': 'TRACKER_ENDED',
                'amount': 50000,
                'currency': 'PKR',
            },
        }

        first_response = self.post_webhook(payload)
        duplicate_response = self.post_webhook(payload)

        payment.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(payment.status, Payment.STATUS_PAID)
        self.assertEqual(donation.status, 'completed')
        self.assertEqual(donation.transaction_id, payment.tracker_token)
        self.assertEqual(PaymentWebhookEvent.objects.count(), 1)

    def test_invalid_signature_and_amount_mismatch_never_mark_paid(self):
        donation = self.create_donation()
        payment = Payment.objects.create(
            initiated_by=self.donor,
            donation=donation,
            purpose=Payment.PURPOSE_DONATION,
            amount=Decimal('500.00'),
            tracker_token='track_donation_2',
        )
        payload = {
            'token': 'evt_donation_2',
            'type': 'payment.succeeded',
            'data': {
                'tracker': payment.tracker_token,
                'state': 'TRACKER_ENDED',
                'amount': 49900,
                'currency': 'PKR',
            },
        }
        invalid_signature_response = self.client.post(
            reverse('safepay_webhook'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_SFPY_SIGNATURE='invalid',
        )
        mismatch_response = self.post_webhook(payload)

        payment.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(invalid_signature_response.status_code, 400)
        self.assertEqual(mismatch_response.status_code, 400)
        self.assertEqual(payment.status, Payment.STATUS_PENDING)
        self.assertEqual(donation.status, 'pending')
        self.assertFalse(PaymentWebhookEvent.objects.exists())

    def test_return_redirect_does_not_confirm_payment(self):
        donation = self.create_donation()
        payment = Payment.objects.create(
            initiated_by=self.donor,
            donation=donation,
            purpose=Payment.PURPOSE_DONATION,
            amount=Decimal('500.00'),
            tracker_token='track_return_only',
        )
        self.client.force_login(self.donor)

        response = self.client.get(reverse('payment_return'), {'tracker': payment.tracker_token})

        payment.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Payment is being verified')
        self.assertEqual(payment.status, Payment.STATUS_PENDING)

    def test_payment_history_is_available_to_donors_sponsors_and_admins(self):
        donation = self.create_donation()
        donation_payment = Payment.objects.create(
            initiated_by=self.donor,
            donation=donation,
            purpose=Payment.PURPOSE_DONATION,
            amount=donation.amount,
            tracker_token='track_donor_history',
        )
        sponsorship = self.create_sponsorship()
        sponsor_payment = Payment.objects.create(
            initiated_by=self.sponsor,
            sponsorship=sponsorship,
            purpose=Payment.PURPOSE_SPONSORSHIP,
            amount=sponsorship.monthly_amount,
            tracker_token='track_sponsor_history',
            status=Payment.STATUS_PAID,
            paid_at=timezone.now(),
        )

        self.client.force_login(self.donor)
        donor_response = self.client.get(reverse('donor_donation_detail', args=[donation.pk]))
        self.assertContains(donor_response, donation_payment.tracker_token)
        self.assertContains(donor_response, 'Pay securely')

        self.client.force_login(self.sponsor)
        sponsor_response = self.client.get(reverse('sponsor_dashboard'), {'section': 'payments'})
        child_response = self.client.get(reverse('sponsor_child_detail', args=[self.child.pk]))
        self.assertContains(sponsor_response, sponsor_payment.tracker_token)
        self.assertContains(child_response, 'Monthly sponsorship payment')
        self.assertContains(child_response, sponsor_payment.tracker_token)

        admin = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=admin, role=AccountProfile.ROLE_ADMIN)
        self.client.force_login(admin)
        admin_response = self.client.get(reverse('sponsorship_detail', args=[sponsorship.pk]))
        self.assertContains(admin_response, 'Verified Payment History')
        self.assertContains(admin_response, sponsor_payment.tracker_token)

    def test_admin_sponsorship_payment_stat_counts_only_verified_payments_this_month(self):
        sponsorship = self.create_sponsorship()
        Payment.objects.create(
            initiated_by=self.sponsor,
            sponsorship=sponsorship,
            purpose=Payment.PURPOSE_SPONSORSHIP,
            amount=Decimal('7500.00'),
            status=Payment.STATUS_PAID,
            paid_at=timezone.now(),
        )
        Payment.objects.create(
            initiated_by=self.sponsor,
            sponsorship=sponsorship,
            purpose=Payment.PURPOSE_SPONSORSHIP,
            amount=Decimal('2500.00'),
            status=Payment.STATUS_PENDING,
        )

        self.assertEqual(
            stats()['monthly_sponsorship_payments'],
            Decimal('7500.00'),
        )

    def test_failed_webhook_allows_new_donation_attempt(self):
        donation = self.create_donation()
        payment = Payment.objects.create(
            initiated_by=self.donor,
            donation=donation,
            purpose=Payment.PURPOSE_DONATION,
            amount=Decimal('500.00'),
            tracker_token='track_donation_3',
        )
        response = self.post_webhook({
            'token': 'evt_donation_3',
            'type': 'payment.failed',
            'data': {'tracker': payment.tracker_token},
        })

        payment.refresh_from_db()
        donation.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.status, Payment.STATUS_FAILED)
        self.assertEqual(donation.status, 'failed')

        with patch(
            'payments.views.create_checkout_url',
            return_value='https://sandbox.api.getsafepay.com/embedded/?checkout=2',
        ):
            self.client.force_login(self.donor)
            retry_response = self.client.post(reverse('donation_checkout', args=[donation.pk]))

        self.assertEqual(retry_response.status_code, 302)
        self.assertEqual(Payment.objects.filter(donation=donation).count(), 2)

    def test_valid_sponsorship_webhook_updates_payment_dates(self):
        sponsorship = self.create_sponsorship()
        payment = Payment.objects.create(
            initiated_by=self.sponsor,
            sponsorship=sponsorship,
            purpose=Payment.PURPOSE_SPONSORSHIP,
            amount=Decimal('7500.00'),
            tracker_token='track_sponsorship_1',
        )

        response = self.post_webhook({
            'token': 'evt_sponsorship_1',
            'type': 'payment.succeeded',
            'data': {
                'tracker': payment.tracker_token,
                'state': 'TRACKER_ENDED',
                'amount': 750000,
                'currency': 'PKR',
            },
        })

        payment.refresh_from_db()
        sponsorship.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.status, Payment.STATUS_PAID)
        self.assertEqual(sponsorship.payment_method, 'Safepay')
        self.assertEqual(sponsorship.last_payment_date, timezone.localdate())
        self.assertGreater(sponsorship.next_payment_date, timezone.localdate())

    def test_sponsor_child_details_unlock_only_after_verified_safepay_payment(self):
        sponsorship = self.create_sponsorship()
        education = EducationRecord.objects.create(
            child=self.child,
            grade_level='class_3',
            attendance_percent='92.00',
        )
        payment = Payment.objects.create(
            initiated_by=self.sponsor,
            sponsorship=sponsorship,
            purpose=Payment.PURPOSE_SPONSORSHIP,
            amount=sponsorship.monthly_amount,
            tracker_token='track_sponsor_unlock',
        )
        self.client.force_login(self.sponsor)

        locked_response = self.client.get(
            reverse('sponsor_child_detail', args=[self.child.pk]),
        )
        tracking_before_payment = self.client.get(
            reverse('sponsor_education_tracking', args=[self.child.pk]),
        )
        return_response = self.client.get(
            reverse('payment_return'),
            {'tracker': payment.tracker_token},
        )
        locked_response_after_return = self.client.get(
            reverse('sponsor_child_detail', args=[self.child.pk]),
        )

        self.assertContains(locked_response, 'Complete your first payment')
        self.assertNotContains(locked_response, self.child.full_name)
        self.assertNotContains(locked_response, self.child.child_id)
        self.assertEqual(tracking_before_payment.status_code, 404)
        self.assertContains(return_response, 'Payment is being verified')
        self.assertContains(locked_response_after_return, 'Complete your first payment')

        webhook_response = self.post_webhook({
            'token': 'evt_sponsor_unlock',
            'type': 'payment.succeeded',
            'data': {
                'tracker': payment.tracker_token,
                'state': 'TRACKER_ENDED',
                'amount': 750000,
                'currency': 'PKR',
            },
        })

        detail_after_payment = self.client.get(
            reverse('sponsor_child_detail', args=[self.child.pk]),
        )
        education_after_payment = self.client.get(
            reverse('sponsor_education_tracking', args=[self.child.pk]),
        )

        self.assertEqual(webhook_response.status_code, 200)
        self.assertContains(detail_after_payment, self.child.full_name)
        self.assertContains(detail_after_payment, self.child.child_id)
        self.assertContains(education_after_payment, education.get_grade_level_display())
