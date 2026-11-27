from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import AccountProfile
from accounts.views.sponsor_views import SponsorApplicationForm, add_calendar_month
from children.models import Attendance, Child, EducationRecord, HealthRecord
from meals.models import MealRecord
from payments.models import Payment
from staff_management.models import StaffMember

from .models import Notification, Sponsorship, SponsorshipConversation, SponsorshipMessage


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_HOST='smtp.test',
)
class SponsorWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.sponsor = user_model.objects.create_user(
            username='sponsor',
            email='sponsor@example.com',
            password='test-password',
            first_name='Sponsor',
        )
        AccountProfile.objects.create(user=self.sponsor, role=AccountProfile.ROLE_SPONSOR)
        self.child = Child.objects.create(
            child_id='CH-100',
            full_name='Test Child',
            education_level='Primary',
        )

    def create_staff(self):
        user = get_user_model().objects.create_user(
            username='staff',
            email='staff@example.com',
            password='test-password',
            first_name='Care',
        )
        AccountProfile.objects.create(user=user, role=AccountProfile.ROLE_STAFF)
        staff_member = StaffMember.objects.create(
            user=user,
            staff_id='ST-100',
            position='Caretaker',
            department='Child Care',
        )
        return user, staff_member

    def create_active_sponsorship(self):
        return Sponsorship.objects.create(
            sponsor=self.sponsor,
            sponsor_code='SP-2026-0001',
            sponsor_name='Sponsor',
            monthly_amount='5000.00',
            start_date=date(2026, 1, 15),
            status='active',
            child=self.child,
        )

    def create_verified_payment(self, sponsorship):
        return Payment.objects.create(
            initiated_by=self.sponsor,
            sponsorship=sponsorship,
            purpose=Payment.PURPOSE_SPONSORSHIP,
            amount=sponsorship.monthly_amount,
            status=Payment.STATUS_PAID,
            paid_at=timezone.now(),
        )

    def test_application_form_requires_valid_contact_details_and_terms(self):
        form = SponsorApplicationForm(data={
            'monthly_amount': '5000',
            'start_date': timezone.localdate().isoformat(),
            'phone': '+92 300 1234567',
            'cnic': '12345-1234567-1',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('terms_accepted', form.errors)

        form = SponsorApplicationForm(data={
            'monthly_amount': '5000',
            'start_date': timezone.localdate().isoformat(),
            'phone': '+92 300 1234567',
            'cnic': '12345-1234567-1',
            'terms_accepted': 'on',
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['cnic'], '12345-1234567-1')

    def test_month_commitment_date_uses_calendar_month(self):
        self.assertEqual(add_calendar_month(date(2026, 1, 31)), date(2026, 2, 28))
        self.assertEqual(add_calendar_month(date(2026, 12, 31)), date(2027, 1, 31))

    def test_application_page_renders_contact_and_terms_fields(self):
        self.client.force_login(self.sponsor)

        response = self.client.get(reverse('sponsor_application'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phone Number')
        self.assertContains(response, 'CNIC')
        self.assertContains(response, 'minimum commitment of one calendar month')
        self.assertNotContains(response, 'Preferred Payment Method')
        self.assertContains(response, 'terms_accepted')

    def test_account_with_current_sponsorship_cannot_request_another(self):
        self.create_active_sponsorship()
        self.client.force_login(self.sponsor)

        response = self.client.get(reverse('sponsor_application'))

        self.assertRedirects(response, reverse('sponsor_dashboard'))
        self.assertEqual(Sponsorship.objects.filter(sponsor=self.sponsor).count(), 1)

        dashboard = self.client.get(reverse('sponsor_dashboard'))
        self.assertFalse(dashboard.context['can_request_sponsorship'])
        self.assertNotContains(dashboard, 'Request Sponsorship')

    def test_ended_sponsorship_does_not_block_a_new_request(self):
        previous = self.create_active_sponsorship()
        previous.status = 'ended'
        previous.save(update_fields=['status'])
        self.client.force_login(self.sponsor)

        response = self.client.post(reverse('sponsor_application'), {
            'monthly_amount': '5000',
            'payment_method': 'Bank Transfer',
            'start_date': timezone.localdate().isoformat(),
            'phone': '+92 300 1234567',
            'cnic': '12345-1234567-1',
            'terms_accepted': 'on',
        })

        self.assertRedirects(response, reverse('sponsor_dashboard'))
        self.assertEqual(
            Sponsorship.objects.filter(sponsor=self.sponsor, status='pending').count(),
            1,
        )

    def test_database_allows_only_one_current_sponsorship_per_account(self):
        current = self.create_active_sponsorship()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Sponsorship.objects.create(
                    sponsor=self.sponsor,
                    sponsor_code='SP-2026-0002',
                    sponsor_name='Sponsor',
                    status='pending',
                )

        current.status = 'ended'
        current.save(update_fields=['status'])
        replacement = Sponsorship.objects.create(
            sponsor=self.sponsor,
            sponsor_code='SP-2026-0002',
            sponsor_name='Sponsor',
            status='pending',
        )
        self.assertEqual(replacement.status, 'pending')

    def test_sponsorship_with_payment_history_cannot_be_deleted(self):
        sponsorship = self.create_active_sponsorship()
        self.child.sponsor_status = 'sponsored'
        self.child.save(update_fields=['sponsor_status'])
        payment = Payment.objects.create(
            initiated_by=self.sponsor,
            sponsorship=sponsorship,
            purpose=Payment.PURPOSE_SPONSORSHIP,
            amount=sponsorship.monthly_amount,
        )
        admin = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=admin, role=AccountProfile.ROLE_ADMIN)
        self.client.force_login(admin)
        delete_url = reverse('sponsorship_delete', args=[sponsorship.pk])

        confirmation = self.client.get(delete_url)
        response = self.client.post(delete_url, follow=True)

        self.assertContains(confirmation, 'cannot be deleted')
        self.assertNotContains(confirmation, 'Yes, Delete')
        self.assertEqual(response.redirect_chain[-1][0], reverse('sponsorship_detail', args=[sponsorship.pk]))
        self.assertContains(response, 'End the sponsorship instead')
        self.assertTrue(Sponsorship.objects.filter(pk=sponsorship.pk).exists())
        self.assertTrue(Payment.objects.filter(pk=payment.pk).exists())
        self.child.refresh_from_db()
        self.assertEqual(self.child.sponsor_status, 'sponsored')

    def test_sponsorship_without_payment_history_can_still_be_deleted(self):
        sponsorship = self.create_active_sponsorship()
        self.child.sponsor_status = 'sponsored'
        self.child.save(update_fields=['sponsor_status'])
        admin = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=admin, role=AccountProfile.ROLE_ADMIN)
        self.client.force_login(admin)

        response = self.client.post(
            reverse('sponsorship_delete', args=[sponsorship.pk]),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('sponsorship_list'))
        self.assertFalse(Sponsorship.objects.filter(pk=sponsorship.pk).exists())
        self.child.refresh_from_db()
        self.assertEqual(self.child.sponsor_status, 'available')

    def test_admin_can_end_sponsorship_without_removing_protected_payment_history(self):
        sponsorship = self.create_active_sponsorship()
        self.child.sponsor_status = 'sponsored'
        self.child.save(update_fields=['sponsor_status'])
        payment = Payment.objects.create(
            initiated_by=self.sponsor,
            sponsorship=sponsorship,
            purpose=Payment.PURPOSE_SPONSORSHIP,
            amount=sponsorship.monthly_amount,
        )
        admin = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=admin, role=AccountProfile.ROLE_ADMIN)
        self.client.force_login(admin)

        response = self.client.post(
            reverse('sponsorship_update', args=[sponsorship.pk]),
            {
                'sponsor_code': sponsorship.sponsor_code,
                'sponsor_name': sponsorship.sponsor_name,
                'cnic': sponsorship.cnic,
                'phone': sponsorship.phone,
                'email': sponsorship.email,
                'child': self.child.pk,
                'monthly_amount': sponsorship.monthly_amount,
                'start_date': sponsorship.start_date.isoformat(),
                'payment_method': sponsorship.payment_method,
                'last_payment_date': '',
                'next_payment_date': '',
                'status': 'ended',
                'ai_match_score': sponsorship.ai_match_score,
            },
        )

        self.assertRedirects(response, reverse('sponsorship_detail', args=[sponsorship.pk]))
        sponsorship.refresh_from_db()
        self.child.refresh_from_db()
        self.assertEqual(sponsorship.status, 'ended')
        self.assertEqual(self.child.sponsor_status, 'available')
        self.assertTrue(Payment.objects.filter(pk=payment.pk).exists())

    def test_sponsor_application_persists_consent_and_notifies_participants(self):
        admin = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=admin, role=AccountProfile.ROLE_ADMIN)
        self.client.force_login(self.sponsor)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse('sponsor_application'), {
                'monthly_amount': '5000',
                'payment_method': 'Bank Transfer',
                'start_date': timezone.localdate().isoformat(),
                'phone': '+92 300 1234567',
                'cnic': '12345-1234567-1',
                'terms_accepted': 'on',
            })

        self.assertRedirects(response, reverse('sponsor_dashboard'))
        sponsorship = Sponsorship.objects.get(sponsor=self.sponsor)
        self.assertEqual(sponsorship.minimum_commitment_end_date, add_calendar_month(timezone.localdate()))
        self.assertEqual(sponsorship.agreement_version, 'sponsor-terms-v1')
        self.assertIsNotNone(sponsorship.agreement_accepted_at)
        self.sponsor.refresh_from_db()
        self.assertEqual(self.sponsor.account_profile.phone, '+92 300 1234567')
        self.assertEqual(Notification.objects.filter(recipient=self.sponsor).count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=admin).count(), 1)
        self.assertEqual(len(mail.outbox), 2)

    def test_admin_matching_notifies_the_sponsor(self):
        admin = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=admin, role=AccountProfile.ROLE_ADMIN)
        sponsorship = Sponsorship.objects.create(
            sponsor=self.sponsor,
            sponsor_code='SP-2026-0001',
            sponsor_name='Sponsor',
            monthly_amount='5000.00',
            start_date=date(2026, 1, 15),
            status='pending',
        )
        self.client.force_login(admin)

        response = self.client.post(reverse('sponsorship_approve', args=[sponsorship.pk]))

        self.assertRedirects(response, reverse('sponsorship_detail', args=[sponsorship.pk]))
        sponsorship.refresh_from_db()
        self.child.refresh_from_db()
        self.assertEqual(sponsorship.status, 'active')
        self.assertEqual(sponsorship.child, self.child)
        self.assertEqual(self.child.sponsor_status, 'sponsored')
        self.assertTrue(Notification.objects.filter(
            recipient=self.sponsor,
            title='Sponsorship approved and matched',
        ).exists())

    def test_approved_sponsor_can_view_tracking_and_new_record_notifies_them(self):
        sponsorship = self.create_active_sponsorship()
        self.create_verified_payment(sponsorship)
        HealthRecord.objects.create(
            child=self.child,
            last_checkup=date(2026, 1, 12),
            doctor_name='Clinic Doctor',
            status='healthy',
        )
        EducationRecord.objects.create(child=self.child, grade_level='class_3')
        Attendance.objects.create(child=self.child, date=date(2026, 1, 13), status='present')
        MealRecord.objects.create(
            child=self.child,
            date=date(2026, 1, 13),
            meal_type='lunch',
            scheduled_food='Rice and vegetables',
            status='ate_fully',
        )
        self.client.force_login(self.sponsor)

        dashboard_response = self.client.get(reverse('sponsor_dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, 'Health Tracking')
        self.assertContains(dashboard_response, 'Education Tracking')
        self.assertContains(dashboard_response, 'Meal Tracking')
        self.assertNotContains(dashboard_response, 'Recent Attendance')
        self.assertNotContains(dashboard_response, 'Rice and vegetables')
        nav_labels = [item['label'] for item in dashboard_response.context['nav_items']]
        self.assertNotIn('Sponsorship Request', nav_labels)
        self.assertNotIn('AI Matching', nav_labels)

        response = self.client.get(reverse('sponsor_child_detail', args=[self.child.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Health History')
        self.assertNotContains(response, 'Recent Meal Records')
        health_response = self.client.get(reverse('sponsor_health_tracking', args=[self.child.pk]))
        education_response = self.client.get(reverse('sponsor_education_tracking', args=[self.child.pk]))
        meals_response = self.client.get(reverse('sponsor_meal_tracking', args=[self.child.pk]))
        self.assertContains(health_response, 'Clinic Doctor')
        self.assertContains(education_response, 'Attendance')
        self.assertContains(meals_response, 'Rice and vegetables')
        self.assertEqual(Notification.objects.filter(recipient=self.sponsor).count(), 4)

    def test_other_sponsor_cannot_see_private_tracking(self):
        self.create_active_sponsorship()
        other_sponsor = get_user_model().objects.create_user(
            username='other-sponsor',
            email='other@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=other_sponsor, role=AccountProfile.ROLE_SPONSOR)
        HealthRecord.objects.create(
            child=self.child,
            last_checkup=date(2026, 1, 12),
            doctor_name='Private Doctor',
            status='healthy',
        )
        self.client.force_login(other_sponsor)

        response = self.client.get(reverse('sponsor_child_detail', args=[self.child.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, 'Health Tracking', status_code=404)
        self.assertNotContains(response, 'Private Doctor', status_code=404)

    def test_sponsor_and_staff_can_exchange_private_messages(self):
        sponsorship = self.create_active_sponsorship()
        self.create_verified_payment(sponsorship)
        staff_user, staff_member = self.create_staff()
        self.child.caretakers.add(staff_member)
        self.client.force_login(self.sponsor)

        response = self.client.post(
            reverse('sponsor_message_send', args=[self.child.pk]),
            {'staff': staff_member.pk, 'body': 'Could you share a progress update?'},
        )

        self.assertEqual(response.status_code, 302)
        conversation = SponsorshipConversation.objects.get(sponsorship=sponsorship, staff=staff_member)
        self.assertRedirects(response, reverse('sponsor_message_thread', args=[conversation.pk]))
        self.assertEqual(SponsorshipMessage.objects.filter(conversation=conversation).count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=staff_user).count(), 1)
        inbox_response = self.client.get(reverse('sponsorship_message_inbox'))
        self.assertEqual(inbox_response.status_code, 200)
        self.assertContains(inbox_response, reverse('sponsor_dashboard') + '?section=overview')
        self.assertContains(inbox_response, reverse('sponsor_message_inbox'))
        self.assertContains(inbox_response, reverse('sponsor_message_thread', args=[conversation.pk]))
        sponsor_inbox_response = self.client.get(reverse('sponsor_message_inbox'))
        self.assertEqual(sponsor_inbox_response.status_code, 200)
        self.assertContains(sponsor_inbox_response, reverse('sponsor_message_thread', args=[conversation.pk]))
        thread_response = self.client.get(
            reverse('sponsorship_message_thread', args=[conversation.pk]),
        )
        notification = Notification.objects.get(recipient=staff_user)
        self.assertEqual(notification.title, 'New message about an assigned child')
        self.assertEqual(notification.url, reverse('caretaker_messages'))
        self.assertEqual(
            self.client.get(reverse('sponsorship_message_inbox')).status_code,
            200,
        )
        self.assertEqual(thread_response.status_code, 200)
        self.assertContains(thread_response, reverse('sponsor_dashboard') + '?section=overview')
        self.assertContains(thread_response, reverse('sponsor_message_inbox'))
        sponsor_thread_response = self.client.get(reverse('sponsor_message_thread', args=[conversation.pk]))
        self.assertEqual(sponsor_thread_response.status_code, 200)
        notification_response = self.client.get(reverse('notification_list'))
        self.assertEqual(notification_response.status_code, 200)
        self.assertContains(notification_response, reverse('sponsor_dashboard') + '?section=overview')

        self.client.force_login(staff_user)
        staff_inbox_response = self.client.get(reverse('sponsorship_message_inbox'))
        self.assertContains(staff_inbox_response, '1 unread')
        caretaker_inbox = self.client.get(reverse('caretaker_messages'))
        self.assertEqual(caretaker_inbox.status_code, 200)
        self.assertContains(caretaker_inbox, 'Could you share a progress update?')
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)
        self.assertEqual(
            self.client.get(reverse('sponsorship_message_thread', args=[conversation.pk])).status_code,
            200,
        )
        response = self.client.post(
            reverse('sponsorship_message_thread', args=[conversation.pk]),
            {'body': 'I will share the latest update.'},
        )

        self.assertRedirects(response, reverse('sponsorship_message_thread', args=[conversation.pk]))
        self.assertEqual(SponsorshipMessage.objects.filter(conversation=conversation).count(), 2)
        self.assertEqual(Notification.objects.filter(recipient=self.sponsor).count(), 1)

        unrelated_user = get_user_model().objects.create_user(
            username='unrelated',
            email='unrelated@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=unrelated_user, role=AccountProfile.ROLE_SPONSOR)
        self.client.force_login(unrelated_user)
        self.assertEqual(
            self.client.get(reverse('sponsorship_message_thread', args=[conversation.pk])).status_code,
            403,
        )

    def test_sponsor_dashboard_shows_tracking_links_and_unread_activity(self):
        sponsorship = self.create_active_sponsorship()
        self.create_verified_payment(sponsorship)
        staff_user, staff_member = self.create_staff()
        conversation = SponsorshipConversation.objects.create(
            sponsorship=sponsorship,
            staff=staff_member,
        )
        SponsorshipMessage.objects.create(
            conversation=conversation,
            sender=staff_user,
            body='A new progress update is ready.',
        )
        Notification.objects.create(
            recipient=self.sponsor,
            title='Progress update available',
            body='A new health update is ready to review.',
        )
        self.client.force_login(self.sponsor)

        response = self.client.get(reverse('sponsor_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('sponsor_health_tracking', args=[self.child.pk]))
        self.assertContains(response, reverse('sponsor_education_tracking', args=[self.child.pk]))
        self.assertContains(response, reverse('sponsor_meal_tracking', args=[self.child.pk]))
        self.assertContains(response, 'New activity')
        self.assertContains(response, 'Progress update available')
        self.assertContains(response, 'A new progress update is ready.')
        self.assertContains(response, '1 unread messages')
        self.assertContains(response, '1 unread notifications')

        inbox_response = self.client.get(reverse('sponsorship_message_inbox'))
        self.assertContains(inbox_response, '1 unread')

    def test_sponsor_tracking_pages_are_separate_and_only_show_their_matched_child(self):
        sponsorship = self.create_active_sponsorship()
        self.create_verified_payment(sponsorship)
        HealthRecord.objects.create(
            child=self.child,
            last_checkup=date(2026, 2, 10),
            doctor_name='Private Pediatrician',
        )
        education = EducationRecord.objects.create(
            child=self.child,
            grade_level='class_5',
            attendance_percent='92.00',
        )
        MealRecord.objects.create(
            child=self.child,
            date=date(2026, 2, 11),
            meal_type='lunch',
            scheduled_food='Rice and vegetables',
            status='ate_fully',
        )
        self.client.force_login(self.sponsor)

        health_response = self.client.get(reverse('sponsor_health_tracking', args=[self.child.pk]))
        education_response = self.client.get(reverse('sponsor_education_tracking', args=[self.child.pk]))
        meals_response = self.client.get(reverse('sponsor_meal_tracking', args=[self.child.pk]))

        self.assertContains(health_response, 'Health History')
        self.assertContains(health_response, 'Private Pediatrician')
        self.assertContains(education_response, education.get_grade_level_display())
        self.assertContains(meals_response, 'Rice and vegetables')
        self.assertContains(
            health_response,
            reverse('sponsor_health_tracking', args=[self.child.pk]),
        )
        self.assertNotContains(
            self.client.get(reverse('sponsor_child_detail', args=[self.child.pk])),
            'Private Pediatrician',
        )

        unrelated_child = Child.objects.create(child_id='CH-UNRELATED', full_name='Unrelated Child')
        self.assertEqual(
            self.client.get(reverse('sponsor_health_tracking', args=[unrelated_child.pk])).status_code,
            404,
        )

    def test_sponsor_child_access_and_communication_require_verified_payment(self):
        sponsorship = self.create_active_sponsorship()
        staff_user, staff_member = self.create_staff()
        conversation = SponsorshipConversation.objects.create(
            sponsorship=sponsorship,
            staff=staff_member,
        )
        SponsorshipMessage.objects.create(
            conversation=conversation,
            sender=staff_user,
            body='Private child progress update.',
        )
        HealthRecord.objects.create(
            child=self.child,
            last_checkup=date(2026, 2, 10),
            doctor_name='Private Pediatrician',
        )
        self.client.force_login(self.sponsor)

        dashboard_response = self.client.get(reverse('sponsor_dashboard'))
        detail_response = self.client.get(reverse('sponsor_child_detail', args=[self.child.pk]))
        health_response = self.client.get(reverse('sponsor_health_tracking', args=[self.child.pk]))
        inbox_response = self.client.get(reverse('sponsorship_message_inbox'))
        thread_response = self.client.get(
            reverse('sponsorship_message_thread', args=[conversation.pk]),
        )
        send_response = self.client.post(
            reverse('sponsor_message_send', args=[self.child.pk]),
            {'staff': staff_member.pk, 'body': 'Please share an update.'},
        )

        self.assertNotContains(dashboard_response, 'Test Child')
        self.assertNotContains(dashboard_response, reverse('sponsor_health_tracking', args=[self.child.pk]))
        self.assertContains(dashboard_response, 'Details unlock after first verified payment')
        self.assertContains(detail_response, 'Complete your first payment')
        self.assertNotContains(detail_response, 'Test Child')
        self.assertNotContains(detail_response, 'CH-100')
        self.assertEqual(health_response.status_code, 404)
        self.assertNotContains(inbox_response, 'Private child progress update.')
        self.assertNotContains(inbox_response, 'Test Child')
        self.assertEqual(thread_response.status_code, 403)
        self.assertEqual(send_response.status_code, 403)
        self.assertEqual(SponsorshipMessage.objects.filter(conversation=conversation).count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.sponsor).count(), 0)
        self.assertEqual(Notification.objects.filter(recipient=staff_user).count(), 0)

    @patch('sponsorships.views.timezone.localdate', return_value=date(2026, 2, 28))
    def test_sponsor_cannot_end_before_minimum_commitment(self, mocked_localdate):
        sponsorship = self.create_active_sponsorship()
        sponsorship.minimum_commitment_end_date = date(2026, 3, 1)
        sponsorship.save(update_fields=['minimum_commitment_end_date'])
        self.client.force_login(self.sponsor)

        response = self.client.post(reverse('sponsor_cancel_sponsorship', args=[sponsorship.pk]))

        self.assertRedirects(response, reverse('sponsor_child_detail', args=[self.child.pk]))
        sponsorship.refresh_from_db()
        self.assertEqual(sponsorship.status, 'active')
        self.assertIsNone(sponsorship.ended_at)

    @patch('sponsorships.views.timezone.localdate', return_value=date(2026, 3, 1))
    def test_sponsor_can_end_after_minimum_commitment(self, mocked_localdate):
        sponsorship = self.create_active_sponsorship()
        sponsorship.minimum_commitment_end_date = date(2026, 3, 1)
        sponsorship.save(update_fields=['minimum_commitment_end_date'])
        self.child.sponsor_status = 'sponsored'
        self.child.save(update_fields=['sponsor_status'])
        self.client.force_login(self.sponsor)

        response = self.client.post(reverse('sponsor_cancel_sponsorship', args=[sponsorship.pk]))

        self.assertRedirects(response, reverse('sponsor_dashboard'))
        sponsorship.refresh_from_db()
        self.child.refresh_from_db()
        self.assertEqual(sponsorship.status, 'ended')
        self.assertEqual(sponsorship.ended_at, date(2026, 3, 1))
        self.assertEqual(self.child.sponsor_status, 'available')
        self.assertTrue(Notification.objects.filter(recipient=self.sponsor, title='Sponsorship ended').exists())

    def test_notification_can_only_be_marked_read_by_its_recipient(self):
        notification = Notification.objects.create(
            recipient=self.sponsor,
            title='Private notice',
            body='This notice belongs to the sponsor.',
        )
        other_user = get_user_model().objects.create_user(
            username='other',
            email='other@example.com',
            password='test-password',
        )
        AccountProfile.objects.create(user=other_user, role=AccountProfile.ROLE_SPONSOR)
        self.client.force_login(other_user)

        self.assertEqual(
            self.client.post(reverse('notification_mark_read', args=[notification.pk])).status_code,
            404,
        )
        notification.refresh_from_db()
        self.assertIsNone(notification.read_at)

        self.client.force_login(self.sponsor)
        response = self.client.post(reverse('notification_mark_read', args=[notification.pk]))

        self.assertRedirects(response, reverse('notification_list'))
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)
