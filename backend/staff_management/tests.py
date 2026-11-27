from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import AccountProfile
from children.models import Attendance, Child, Course, EducationRecord, EducationResult, HealthRecord
from meals.models import ChildAllergy, MealRecord, MealSchedule
from sponsorships.models import Sponsorship, SponsorshipConversation, SponsorshipMessage
from .models import CareIncident, DailyCareLog, StaffMember


User = get_user_model()


class TeacherDashboardTests(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher@example.com',
            password='test-password-123',
        )
        AccountProfile.objects.create(user=self.teacher_user, role=AccountProfile.ROLE_STAFF)
        self.teacher = StaffMember.objects.create(
            user=self.teacher_user,
            staff_id='ST001',
            position='Teacher',
            department='Education',
        )

    def test_staff_login_redirects_teacher_to_teacher_dashboard(self):
        response = self.client.post(reverse('admin_login'), {
            'email': 'teacher@example.com',
            'role': AccountProfile.ROLE_STAFF,
            'password': 'test-password-123',
        })

        self.assertRedirects(response, reverse('teacher_dashboard'))

    def test_staff_dashboard_route_redirects_teachers_to_their_workspace(self):
        self.client.force_login(self.teacher_user)

        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, reverse('teacher_dashboard'))

    def test_anonymous_teacher_dashboard_request_uses_shared_staff_login(self):
        response = self.client.get(reverse('teacher_dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/admin_login/?role=staff', response['Location'])

    def test_dashboard_only_counts_results_for_assigned_students(self):
        assigned_child = Child.objects.create(child_id='CH001', full_name='Assigned Student')
        other_child = Child.objects.create(child_id='CH002', full_name='Unassigned Student')
        EducationRecord.objects.create(
            child=assigned_child,
            class_teacher=self.teacher,
            grade_level='class_1',
        )
        EducationRecord.objects.create(child=other_child, grade_level='class_2')
        course = Course.objects.create(title='Reading', code='READ-1')
        EducationResult.objects.create(
            child=assigned_child,
            course=course,
            teacher=self.teacher,
            term='term_1',
            score=85,
        )
        EducationResult.objects.create(
            child=other_child,
            course=course,
            teacher=self.teacher,
            term='term_1',
            score=45,
        )

        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('teacher_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['student_count'], 1)
        self.assertEqual(response.context['class_count'], 1)
        self.assertEqual(response.context['result_count'], 1)
        self.assertContains(response, 'Assigned Student')
        self.assertNotContains(response, 'Unassigned Student')

    def test_my_students_page_only_lists_students_assigned_to_teacher(self):
        assigned_child = Child.objects.create(child_id='CH101', full_name='Assigned Student')
        other_child = Child.objects.create(child_id='CH102', full_name='Unassigned Student')
        EducationRecord.objects.create(
            child=assigned_child,
            class_teacher=self.teacher,
            grade_level='class_1',
            roll_number='R-101',
        )
        EducationRecord.objects.create(child=other_child, grade_level='class_2')

        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('teacher_students'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['student_count'], 1)
        self.assertContains(response, 'Assigned Student')
        self.assertContains(response, 'R-101')
        self.assertNotContains(response, 'Unassigned Student')
        self.assertContains(response, 'data-admin-sidebar')
        self.assertContains(response, 'data-sidebar-toggle')
        self.assertContains(response, 'theme-toggle-btn')

    def test_teacher_can_mark_and_update_attendance_only_for_assigned_students(self):
        assigned_child = Child.objects.create(child_id='CH201', full_name='Assigned Student')
        other_child = Child.objects.create(child_id='CH202', full_name='Unassigned Student')
        EducationRecord.objects.create(child=assigned_child, class_teacher=self.teacher)
        EducationRecord.objects.create(child=other_child)
        attendance_date = timezone.localdate()
        post_data = {
            'date': attendance_date.isoformat(),
            f'status_{assigned_child.pk}': 'present',
            f'status_{other_child.pk}': 'absent',
        }

        self.client.force_login(self.teacher_user)
        response = self.client.post(reverse('teacher_attendance'), post_data)

        self.assertRedirects(
            response,
            f"{reverse('teacher_attendance')}?date={attendance_date.isoformat()}",
        )
        attendance = Attendance.objects.get(child=assigned_child, date=attendance_date)
        self.assertEqual(attendance.status, 'present')
        self.assertEqual(attendance.marked_by, 'ST001')
        self.assertFalse(Attendance.objects.filter(child=other_child, date=attendance_date).exists())

        response = self.client.get(reverse('teacher_attendance'), {'date': attendance_date.isoformat()})
        self.assertEqual(response.context['students'][0]['status_field'].value(), 'present')

        post_data[f'status_{assigned_child.pk}'] = 'late'
        self.client.post(reverse('teacher_attendance'), post_data)
        attendance.refresh_from_db()
        self.assertEqual(attendance.status, 'late')
        self.assertEqual(Attendance.objects.filter(child=assigned_child, date=attendance_date).count(), 1)

    def test_attendance_requires_status_for_each_assigned_student(self):
        child = Child.objects.create(child_id='CH203', full_name='Assigned Student')
        EducationRecord.objects.create(child=child, class_teacher=self.teacher)
        self.client.force_login(self.teacher_user)

        response = self.client.post(reverse('teacher_attendance'), {
            'date': timezone.localdate().isoformat(),
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(f'status_{child.pk}', response.context['attendance_form'].errors)
        self.assertFalse(Attendance.objects.filter(child=child).exists())

    def test_attendance_rejects_future_dates(self):
        child = Child.objects.create(child_id='CH204', full_name='Assigned Student')
        EducationRecord.objects.create(child=child, class_teacher=self.teacher)
        self.client.force_login(self.teacher_user)
        future_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(reverse('teacher_attendance'), {
            'date': future_date.isoformat(),
            f'status_{child.pk}': 'present',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('date', response.context['attendance_form'].errors)
        self.assertFalse(Attendance.objects.filter(child=child).exists())

    def test_teacher_can_record_and_update_results_for_assigned_students(self):
        child = Child.objects.create(child_id='CH301', full_name='Assigned Student')
        EducationRecord.objects.create(child=child, class_teacher=self.teacher)
        course = Course.objects.create(title='Science', code='SCI-1')
        other_teacher = StaffMember.objects.create(
            staff_id='ST003',
            position='Teacher',
            department='Education',
        )
        self.client.force_login(self.teacher_user)

        response = self.client.post(reverse('teacher_result_create'), {
            'child': child.pk,
            'course': course.pk,
            'teacher': other_teacher.pk,
            'term': 'term_1',
            'score': '92.50',
            'remarks': 'Good work',
        })

        self.assertRedirects(response, reverse('teacher_results'))
        result = EducationResult.objects.get(child=child)
        self.assertEqual(result.teacher, self.teacher)
        self.assertEqual(result.grade, 'A+')

        response = self.client.post(reverse('teacher_result_update', args=[result.pk]), {
            'child': child.pk,
            'course': course.pk,
            'term': 'term_1',
            'score': '72.00',
            'remarks': 'Improving',
        })

        self.assertRedirects(response, reverse('teacher_results'))
        result.refresh_from_db()
        self.assertEqual(result.score, 72)
        self.assertEqual(result.grade, 'B')
        self.assertEqual(result.teacher, self.teacher)

    def test_teacher_cannot_record_a_result_for_unassigned_student(self):
        child = Child.objects.create(child_id='CH302', full_name='Unassigned Student')
        self.client.force_login(self.teacher_user)

        response = self.client.post(reverse('teacher_result_create'), {
            'child': child.pk,
            'term': 'term_1',
            'score': '80',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('child', response.context['form'].errors)
        self.assertFalse(EducationResult.objects.filter(child=child).exists())

    def test_teacher_results_list_only_includes_own_results_for_assigned_students(self):
        assigned_child = Child.objects.create(child_id='CH303', full_name='Assigned Student')
        unassigned_child = Child.objects.create(child_id='CH304', full_name='Unassigned Student')
        EducationRecord.objects.create(child=assigned_child, class_teacher=self.teacher)
        other_teacher = StaffMember.objects.create(
            staff_id='ST004',
            position='Teacher',
            department='Education',
        )
        EducationResult.objects.create(child=assigned_child, teacher=self.teacher, score=85)
        EducationResult.objects.create(child=unassigned_child, teacher=self.teacher, score=60)
        EducationResult.objects.create(child=assigned_child, teacher=other_teacher, score=70)
        self.client.force_login(self.teacher_user)

        response = self.client.get(reverse('teacher_results'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['result_count'], 1)
        self.assertContains(response, 'Assigned Student')
        self.assertNotContains(response, 'Unassigned Student')

    def test_teacher_cannot_edit_another_teachers_result(self):
        child = Child.objects.create(child_id='CH305', full_name='Assigned Student')
        EducationRecord.objects.create(child=child, class_teacher=self.teacher)
        other_teacher = StaffMember.objects.create(
            staff_id='ST005',
            position='Teacher',
            department='Education',
        )
        result = EducationResult.objects.create(child=child, teacher=other_teacher, score=70)
        self.client.force_login(self.teacher_user)

        response = self.client.get(reverse('teacher_result_update', args=[result.pk]))

        self.assertEqual(response.status_code, 404)

    def test_non_teacher_staff_cannot_access_teacher_dashboard(self):
        doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='test-password-123',
        )
        AccountProfile.objects.create(user=doctor_user, role=AccountProfile.ROLE_STAFF)
        StaffMember.objects.create(
            user=doctor_user,
            staff_id='ST002',
            position='Doctor',
            department='Health',
        )

        self.client.force_login(doctor_user)
        for route_name in (
            'teacher_dashboard',
            'teacher_students',
            'teacher_attendance',
            'teacher_results',
        ):
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertRedirects(response, reverse('index'))

    def test_staff_login_requires_an_active_staff_record(self):
        unlinked_user = User.objects.create_user(
            username='unlinked',
            email='unlinked@example.com',
            password='test-password-123',
        )
        AccountProfile.objects.create(user=unlinked_user, role=AccountProfile.ROLE_STAFF)

        response = self.client.post(reverse('admin_login'), {
            'email': 'unlinked@example.com',
            'role': AccountProfile.ROLE_STAFF,
            'password': 'test-password-123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, 'An active staff profile must be linked to this account.')

    def test_account_without_assigned_role_cannot_choose_staff_at_login(self):
        unassigned_user = User.objects.create_user(
            username='unassigned',
            email='unassigned@example.com',
            password='test-password-123',
        )

        response = self.client.post(reverse('admin_login'), {
            'email': 'unassigned@example.com',
            'role': AccountProfile.ROLE_STAFF,
            'password': 'test-password-123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(AccountProfile.objects.filter(user=unassigned_user).exists())
        self.assertContains(response, 'This account does not have an assigned role.')


class DoctorDashboardTests(TestCase):
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='test-password-123',
        )
        AccountProfile.objects.create(user=self.doctor_user, role=AccountProfile.ROLE_STAFF)
        self.doctor = StaffMember.objects.create(
            user=self.doctor_user,
            staff_id='ST101',
            position='Doctor',
            department='Health',
        )

    def test_staff_login_redirects_doctor_to_doctor_dashboard(self):
        response = self.client.post(reverse('admin_login'), {
            'email': 'doctor@example.com',
            'role': AccountProfile.ROLE_STAFF,
            'password': 'test-password-123',
        })

        self.assertRedirects(response, reverse('doctor_dashboard'))

    def test_staff_dashboard_route_redirects_doctors_to_their_workspace(self):
        self.client.force_login(self.doctor_user)

        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, reverse('doctor_dashboard'))

    def test_doctor_dashboard_lists_only_assigned_children_and_health_records(self):
        assigned_child = Child.objects.create(child_id='CH401', full_name='Assigned Patient')
        unassigned_child = Child.objects.create(child_id='CH402', full_name='Unassigned Patient')
        assigned_child.doctors.add(self.doctor)
        HealthRecord.objects.create(
            child=assigned_child,
            last_checkup=timezone.localdate(),
            priority_level='critical',
            follow_up_status='pending',
            follow_up_due=timezone.localdate() + timedelta(days=1),
        )
        HealthRecord.objects.create(
            child=unassigned_child,
            last_checkup=timezone.localdate(),
            priority_level='critical',
            follow_up_status='pending',
            follow_up_due=timezone.localdate() + timedelta(days=1),
        )
        self.client.force_login(self.doctor_user)

        response = self.client.get(reverse('doctor_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['patient_count'], 1)
        self.assertEqual(response.context['critical_record_count'], 1)
        self.assertEqual(response.context['pending_followup_count'], 1)
        self.assertContains(response, 'Assigned Patient')
        self.assertNotContains(response, 'Unassigned Patient')
        self.assertContains(response, 'data-admin-sidebar')
        self.assertContains(response, 'theme-toggle-btn')

    def test_doctor_can_open_only_an_assigned_patient_record(self):
        assigned_child = Child.objects.create(child_id='CH403', full_name='Assigned Patient')
        unassigned_child = Child.objects.create(child_id='CH404', full_name='Unassigned Patient')
        assigned_child.doctors.add(self.doctor)
        HealthRecord.objects.create(
            child=assigned_child,
            last_checkup=timezone.localdate(),
            diagnosis='Seasonal allergies',
        )
        self.client.force_login(self.doctor_user)

        response = self.client.get(reverse('doctor_patient_detail', args=[assigned_child.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Seasonal allergies')
        self.assertEqual(
            self.client.get(reverse('doctor_patient_detail', args=[unassigned_child.pk])).status_code,
            404,
        )

    def test_doctor_can_create_health_record_only_for_assigned_patient(self):
        assigned_child = Child.objects.create(child_id='CH405', full_name='Assigned Patient')
        unassigned_child = Child.objects.create(child_id='CH406', full_name='Unassigned Patient')
        assigned_child.doctors.add(self.doctor)
        self.client.force_login(self.doctor_user)

        form_response = self.client.get(
            reverse('doctor_health_record_create', args=[assigned_child.pk]),
        )
        self.assertEqual(form_response.status_code, 200)
        self.assertNotIn('child', form_response.context['form'].fields)
        self.assertNotIn('doctor_name', form_response.context['form'].fields)

        response = self.client.post(
            reverse('doctor_health_record_create', args=[assigned_child.pk]),
            {
                'child': unassigned_child.pk,
                'doctor_name': 'Someone Else',
                'record_type': 'checkup',
                'last_checkup': timezone.localdate().isoformat(),
                'temperature_c': '37.2',
                'vaccinations': 'pending',
                'status': 'under_care',
                'priority_level': 'high',
                'diagnosis': 'Seasonal allergies',
                'follow_up_status': 'pending',
            },
        )

        self.assertRedirects(
            response,
            reverse('doctor_patient_detail', args=[assigned_child.pk]),
        )
        record = HealthRecord.objects.get(child=assigned_child)
        self.assertEqual(record.doctor_name, 'ST101')
        self.assertEqual(record.diagnosis, 'Seasonal allergies')
        self.assertFalse(HealthRecord.objects.filter(child=unassigned_child).exists())
        self.assertEqual(
            self.client.get(
                reverse('doctor_health_record_create', args=[unassigned_child.pk]),
            ).status_code,
            404,
        )

    def test_doctor_can_update_only_records_for_assigned_patients(self):
        assigned_child = Child.objects.create(child_id='CH407', full_name='Assigned Patient')
        unassigned_child = Child.objects.create(child_id='CH408', full_name='Unassigned Patient')
        assigned_child.doctors.add(self.doctor)
        assigned_record = HealthRecord.objects.create(
            child=assigned_child,
            last_checkup=timezone.localdate(),
            doctor_name='Existing Doctor',
            diagnosis='Initial diagnosis',
        )
        unassigned_record = HealthRecord.objects.create(
            child=unassigned_child,
            last_checkup=timezone.localdate(),
            diagnosis='Private diagnosis',
        )
        self.client.force_login(self.doctor_user)

        response = self.client.post(
            reverse('doctor_health_record_update', args=[assigned_record.pk]),
            {
                'child': unassigned_child.pk,
                'doctor_name': 'Someone Else',
                'record_type': 'checkup',
                'last_checkup': timezone.localdate().isoformat(),
                'vaccinations': 'pending',
                'diagnosis': 'Updated diagnosis',
                'status': 'healthy',
                'priority_level': 'routine',
                'follow_up_status': 'pending',
            },
        )

        self.assertRedirects(
            response,
            reverse('doctor_patient_detail', args=[assigned_child.pk]),
        )
        assigned_record.refresh_from_db()
        self.assertEqual(assigned_record.child, assigned_child)
        self.assertEqual(assigned_record.doctor_name, 'Existing Doctor')
        self.assertEqual(assigned_record.diagnosis, 'Updated diagnosis')
        self.assertEqual(
            self.client.get(
                reverse('doctor_health_record_update', args=[unassigned_record.pk]),
            ).status_code,
            404,
        )

    def test_child_form_only_offers_active_doctor_staff(self):
        from children.forms import ChildForm

        inactive_doctor = StaffMember.objects.create(
            staff_id='ST102',
            position='Doctor',
            department='Health',
            employment_status='inactive',
        )
        teacher = StaffMember.objects.create(
            staff_id='ST103',
            position='Teacher',
            department='Education',
        )

        doctor_ids = set(ChildForm().fields['doctors'].queryset.values_list('pk', flat=True))

        self.assertIn(self.doctor.pk, doctor_ids)
        self.assertNotIn(inactive_doctor.pk, doctor_ids)
        self.assertNotIn(teacher.pk, doctor_ids)


class CaretakerDashboardTests(TestCase):
    def setUp(self):
        self.caretaker_user = User.objects.create_user(
            username='caretaker1',
            email='caretaker@example.com',
            password='test-password-123',
        )
        AccountProfile.objects.create(user=self.caretaker_user, role=AccountProfile.ROLE_STAFF)
        self.caretaker = StaffMember.objects.create(
            user=self.caretaker_user,
            staff_id='ST201',
            position='Care Taker',
            department='Child Care',
        )

    def test_staff_login_redirects_caretaker_to_caretaker_dashboard(self):
        response = self.client.post(reverse('admin_login'), {
            'email': 'caretaker@example.com',
            'role': AccountProfile.ROLE_STAFF,
            'password': 'test-password-123',
        })

        self.assertRedirects(response, reverse('caretaker_dashboard'))

    def test_caretaker_dashboard_shows_only_assigned_children_and_meal_logs(self):
        assigned_child = Child.objects.create(child_id='CH501', full_name='Assigned Child')
        unassigned_child = Child.objects.create(child_id='CH502', full_name='Unassigned Child')
        assigned_child.caretakers.add(self.caretaker)
        today = timezone.localdate()
        MealRecord.objects.create(
            child=assigned_child,
            date=today,
            meal_type='breakfast',
            scheduled_food='Egg and bread',
            status='ate_fully',
            recorded_by=self.caretaker,
        )
        MealRecord.objects.create(
            child=unassigned_child,
            date=today,
            meal_type='lunch',
            scheduled_food='Rice',
            status='refused',
        )
        self.client.force_login(self.caretaker_user)

        response = self.client.get(reverse('caretaker_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['child_count'], 1)
        self.assertEqual(response.context['meal_record_count'], 1)
        self.assertEqual(response.context['refused_meal_count'], 0)
        self.assertContains(response, 'Assigned Child')
        self.assertNotContains(response, 'Unassigned Child')
        self.assertContains(response, 'Education Tracking')
        self.assertContains(response, 'Health Tracking')
        self.assertContains(response, 'Child Messages')
        self.assertContains(response, 'data-admin-sidebar')
        self.assertContains(response, 'theme-toggle-btn')

    def test_caretaker_education_tracking_is_limited_to_class_and_attendance(self):
        assigned_child = Child.objects.create(child_id='CH509', full_name='Assigned Student')
        unassigned_child = Child.objects.create(child_id='CH510', full_name='Unassigned Student')
        EducationRecord.objects.create(
            child=assigned_child,
            grade_level='class_4',
            academic_year='2026-2027',
        )
        assigned_child.caretakers.add(self.caretaker)
        Attendance.objects.create(
            child=assigned_child,
            date=timezone.localdate(),
            status='present',
        )
        Attendance.objects.create(
            child=assigned_child,
            date=timezone.localdate() - timedelta(days=1),
            status='absent',
        )
        EducationResult.objects.create(
            child=assigned_child,
            score=99,
            remarks='Private academic result',
        )
        self.client.force_login(self.caretaker_user)

        response = self.client.get(reverse('caretaker_education_tracking'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assigned Student')
        self.assertContains(response, 'Class 4')
        self.assertContains(response, '2026-2027')
        self.assertContains(response, '50.0%')
        self.assertNotContains(response, 'Unassigned Student')
        self.assertNotContains(response, 'Private academic result')
        self.assertNotContains(response, '99')

    def test_caretaker_health_tracking_shows_limited_health_summary(self):
        assigned_child = Child.objects.create(
            child_id='CH511',
            full_name='Assigned Patient',
            health_status='under_care',
        )
        unassigned_child = Child.objects.create(child_id='CH512', full_name='Unassigned Patient')
        assigned_child.caretakers.add(self.caretaker)
        ChildAllergy.objects.create(
            child=assigned_child,
            allergies='Peanuts',
            dietary_restrictions='No nuts',
        )
        HealthRecord.objects.create(
            child=assigned_child,
            last_checkup=timezone.localdate(),
            priority_level='high',
            follow_up_due=timezone.localdate() + timedelta(days=5),
            follow_up_status='pending',
            diagnosis='Restricted diagnosis details',
        )
        HealthRecord.objects.create(
            child=unassigned_child,
            last_checkup=timezone.localdate(),
            diagnosis='Unassigned private diagnosis',
        )
        self.client.force_login(self.caretaker_user)

        response = self.client.get(reverse('caretaker_health_tracking'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assigned Patient')
        self.assertContains(response, 'Peanuts')
        self.assertContains(response, 'No nuts')
        self.assertContains(response, 'High')
        self.assertNotContains(response, 'Restricted diagnosis details')
        self.assertNotContains(response, 'Unassigned Patient')
        self.assertNotContains(response, 'Unassigned private diagnosis')

    def test_caretaker_can_view_only_messages_for_assigned_children(self):
        sponsor = User.objects.create_user(
            username='message-sponsor',
            email='message-sponsor@example.com',
            password='test-password-123',
        )
        AccountProfile.objects.create(user=sponsor, role=AccountProfile.ROLE_SPONSOR)
        unassigned_sponsor = User.objects.create_user(
            username='unassigned-message-sponsor',
            email='unassigned-message-sponsor@example.com',
            password='test-password-123',
        )
        AccountProfile.objects.create(user=unassigned_sponsor, role=AccountProfile.ROLE_SPONSOR)
        assigned_child = Child.objects.create(child_id='CH513', full_name='Assigned Student')
        unassigned_child = Child.objects.create(child_id='CH514', full_name='Unassigned Student')
        assigned_child.caretakers.add(self.caretaker)
        sponsorship = Sponsorship.objects.create(
            sponsor=sponsor,
            sponsor_code='SP-CARE-001',
            sponsor_name='Test Sponsor',
            monthly_amount='5000.00',
            start_date=timezone.localdate(),
            status='active',
            child=assigned_child,
        )
        unassigned_sponsorship = Sponsorship.objects.create(
            sponsor=unassigned_sponsor,
            sponsor_code='SP-CARE-002',
            sponsor_name='Test Sponsor',
            monthly_amount='5000.00',
            start_date=timezone.localdate(),
            status='active',
            child=unassigned_child,
        )
        other_staff = StaffMember.objects.create(
            staff_id='ST205',
            position='Teacher',
            department='Education',
        )
        assigned_conversation = SponsorshipConversation.objects.create(
            sponsorship=sponsorship,
            staff=self.caretaker,
        )
        assigned_other_staff_conversation = SponsorshipConversation.objects.create(
            sponsorship=sponsorship,
            staff=other_staff,
        )
        unassigned_conversation = SponsorshipConversation.objects.create(
            sponsorship=unassigned_sponsorship,
            staff=self.caretaker,
        )
        SponsorshipMessage.objects.create(
            conversation=assigned_conversation,
            sender=sponsor,
            body='Assigned child progress message',
        )
        SponsorshipMessage.objects.create(
            conversation=assigned_other_staff_conversation,
            sender=sponsor,
            body='Assigned child message for another staff member',
        )
        SponsorshipMessage.objects.create(
            conversation=unassigned_conversation,
            sender=sponsor,
            body='Unassigned child private message',
        )
        self.client.force_login(self.caretaker_user)

        response = self.client.get(reverse('caretaker_messages'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assigned child progress message')
        self.assertNotContains(response, 'Assigned child message for another staff member')
        self.assertNotContains(response, 'Unassigned child private message')
        self.assertNotContains(response, 'Send Reply')

    def test_caretaker_can_log_meals_only_for_assigned_children(self):
        assigned_child = Child.objects.create(child_id='CH503', full_name='Assigned Child')
        unassigned_child = Child.objects.create(child_id='CH504', full_name='Unassigned Child')
        assigned_child.caretakers.add(self.caretaker)
        ChildAllergy.objects.create(
            child=assigned_child,
            allergies='Peanuts',
            dietary_restrictions='No nuts',
        )
        today = timezone.localdate()
        MealSchedule.objects.create(
            day=today.strftime('%A').lower(),
            meal_type='breakfast',
            food_items='Egg and bread',
        )
        self.client.force_login(self.caretaker_user)

        response = self.client.get(reverse('caretaker_meal_log', args=[assigned_child.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Peanuts')
        self.assertContains(response, 'No nuts')

        response = self.client.post(
            reverse('caretaker_meal_log', args=[assigned_child.pk]),
            {
                'date': today.isoformat(),
                'child': unassigned_child.pk,
                'status_breakfast': 'ate_fully',
                'notes_breakfast': 'Finished meal',
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('caretaker_meal_log', args=[assigned_child.pk])}?date={today.isoformat()}",
        )
        meal_record = MealRecord.objects.get(child=assigned_child, date=today, meal_type='breakfast')
        self.assertEqual(meal_record.status, 'ate_fully')
        self.assertEqual(meal_record.recorded_by, self.caretaker)
        self.assertFalse(MealRecord.objects.filter(child=unassigned_child, date=today).exists())
        self.assertEqual(
            self.client.get(reverse('caretaker_meal_log', args=[unassigned_child.pk])).status_code,
            404,
        )

    def test_caretaker_cannot_log_meals_for_future_dates(self):
        child = Child.objects.create(child_id='CH505', full_name='Assigned Child')
        child.caretakers.add(self.caretaker)
        today = timezone.localdate()
        MealSchedule.objects.create(
            day=(today + timedelta(days=1)).strftime('%A').lower(),
            meal_type='breakfast',
            food_items='Oatmeal',
        )
        self.client.force_login(self.caretaker_user)

        response = self.client.post(
            reverse('caretaker_meal_log', args=[child.pk]),
            {
                'date': (today + timedelta(days=1)).isoformat(),
                'status_breakfast': 'ate_fully',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('date', response.context['form'].errors)
        self.assertFalse(MealRecord.objects.filter(child=child).exists())

    def test_child_form_only_offers_active_caretakers(self):
        from children.forms import ChildForm

        inactive_caretaker = StaffMember.objects.create(
            staff_id='ST202',
            position='Caregiver',
            department='Child Care',
            employment_status='inactive',
        )
        teacher = StaffMember.objects.create(
            staff_id='ST203',
            position='Teacher',
            department='Education',
        )

        caretaker_ids = set(ChildForm().fields['caretakers'].queryset.values_list('pk', flat=True))

        self.assertIn(self.caretaker.pk, caretaker_ids)
        self.assertNotIn(inactive_caretaker.pk, caretaker_ids)
        self.assertNotIn(teacher.pk, caretaker_ids)

    def test_non_caretaker_staff_cannot_access_caretaker_workspace(self):
        doctor_user = User.objects.create_user(
            username='doctor2',
            email='doctor2@example.com',
            password='test-password-123',
        )
        AccountProfile.objects.create(user=doctor_user, role=AccountProfile.ROLE_STAFF)
        StaffMember.objects.create(
            user=doctor_user,
            staff_id='ST204',
            position='Doctor',
            department='Health',
        )
        self.client.force_login(doctor_user)

        for route_name in (
            'caretaker_dashboard',
            'caretaker_education_tracking',
            'caretaker_health_tracking',
            'caretaker_messages',
        ):
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertRedirects(response, reverse('index'))

    def test_caretaker_can_save_daily_care_and_handover_for_assigned_child(self):
        child = Child.objects.create(child_id='CH506', full_name='Assigned Child')
        unassigned_child = Child.objects.create(child_id='CH507', full_name='Unassigned Child')
        child.caretakers.add(self.caretaker)
        today = timezone.localdate()
        self.client.force_login(self.caretaker_user)

        response = self.client.post(
            reverse('caretaker_daily_care', args=[child.pk]),
            {
                'date': today.isoformat(),
                'hygiene_status': 'completed',
                'rest_status': 'rested_well',
                'mood': 'calm',
                'notes': 'Participated in activities.',
                'handover_notes': 'Needs a water bottle.',
                'shift': 'night',
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('caretaker_daily_care', args=[child.pk])}?date={today.isoformat()}",
        )
        care_log = DailyCareLog.objects.get(child=child, date=today)
        self.assertEqual(care_log.caretaker, self.caretaker)
        self.assertEqual(care_log.shift, self.caretaker.shift)
        self.assertEqual(care_log.handover_notes, 'Needs a water bottle.')
        self.assertEqual(
            self.client.get(reverse('caretaker_daily_care', args=[unassigned_child.pk])).status_code,
            404,
        )

    def test_caretaker_can_report_incident_and_assigned_doctor_can_review_it(self):
        child = Child.objects.create(child_id='CH508', full_name='Assigned Child')
        child.caretakers.add(self.caretaker)
        doctor_user = User.objects.create_user(
            username='doctor3',
            email='doctor3@example.com',
            password='test-password-123',
        )
        AccountProfile.objects.create(user=doctor_user, role=AccountProfile.ROLE_STAFF)
        doctor = StaffMember.objects.create(
            user=doctor_user,
            staff_id='ST301',
            position='Doctor',
            department='Health',
        )
        child.doctors.add(doctor)
        self.client.force_login(self.caretaker_user)

        response = self.client.post(
            reverse('caretaker_incident_report', args=[child.pk]),
            {
                'category': 'injury',
                'severity': 'high',
                'description': 'Small cut on the left hand.',
                'immediate_action': 'First aid was provided according to center procedure.',
            },
        )

        self.assertRedirects(response, reverse('caretaker_incidents'))
        incident = CareIncident.objects.get(child=child)
        self.assertEqual(incident.reported_by, self.caretaker)
        self.assertEqual(incident.status, 'open')

        self.client.force_login(doctor_user)
        response = self.client.get(reverse('doctor_incidents'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Small cut on the left hand.')
        response = self.client.post(
            reverse('doctor_incident_review', args=[incident.pk]),
            {
                'status': 'reviewed',
                'review_notes': 'Follow-up completed.',
            },
        )

        self.assertRedirects(response, reverse('doctor_incidents'))
        incident.refresh_from_db()
        self.assertEqual(incident.status, 'reviewed')
        self.assertEqual(incident.reviewed_by, doctor)
