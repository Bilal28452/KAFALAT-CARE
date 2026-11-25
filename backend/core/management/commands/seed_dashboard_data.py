from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from children.models import Child, EducationRecord, HealthRecord
from donations.models import Donation
from sponsorships.models import Sponsorship
from staff_management.models import StaffMember


class Command(BaseCommand):
    help = 'Seeds dashboard demo records into the database.'

    def handle(self, *args, **options):
        hassan, _ = Child.objects.update_or_create(
            child_id='CH001',
            defaults={
                'full_name': 'Muhammad Hassan',
                'date_of_birth': date(2018, 3, 15),
                'gender': 'male',
                'health_status': 'healthy',
                'education_level': 'Class 2',
                'sponsor_status': 'sponsored',
                'emergency_contact': '+92 300 1234567',
                'admission_date': date(2023, 9, 15),
            },
        )
        fatima, _ = Child.objects.update_or_create(
            child_id='CH002',
            defaults={
                'full_name': 'Fatima Noor',
                'date_of_birth': date(2017, 6, 22),
                'gender': 'female',
                'health_status': 'under_care',
                'education_level': 'Class 4',
                'sponsor_status': 'available',
                'emergency_contact': '+92 300 2345678',
                'admission_date': date(2023, 10, 20),
            },
        )
        ali, _ = Child.objects.update_or_create(
            child_id='CH003',
            defaults={
                'full_name': 'Ali Raza',
                'date_of_birth': date(2014, 8, 10),
                'gender': 'male',
                'health_status': 'medical_care',
                'education_level': 'Class 6',
                'sponsor_status': 'sponsored',
                'emergency_contact': '+92 300 3456789',
                'admission_date': date(2023, 8, 5),
            },
        )

        HealthRecord.objects.update_or_create(
            child=hassan,
            last_checkup=date(2026, 5, 10),
            defaults={
                'next_checkup': date(2026, 6, 10),
                'blood_type': 'B+',
                'weight': '26 kg',
                'height': '128 cm',
                'vaccinations': 'complete',
                'current_medications': '',
                'allergies': '',
                'medical_history': 'No significant history',
                'doctor_name': 'Dr. Ayesha Khan',
                'status': 'healthy',
            },
        )
        HealthRecord.objects.update_or_create(
            child=fatima,
            last_checkup=date(2026, 5, 14),
            defaults={
                'next_checkup': date(2026, 6, 14),
                'blood_type': 'O+',
                'weight': '28 kg',
                'height': '132 cm',
                'vaccinations': 'complete',
                'current_medications': 'Iron supplement',
                'allergies': '',
                'medical_history': 'Mild anemia',
                'doctor_name': 'Dr. Ayesha Khan',
                'status': 'under_care',
            },
        )

        EducationRecord.objects.update_or_create(
            child=hassan,
            school_name='Govt School #5',
            grade='Class 2',
            defaults={
                'roll_number': '101',
                'attendance_percent': Decimal('94.00'),
                'urdu_marks': Decimal('85.00'),
                'english_marks': Decimal('78.00'),
                'math_marks': Decimal('92.00'),
                'science_marks': Decimal('88.00'),
                'islamiat_marks': Decimal('90.00'),
                'teacher_name': 'Miss Sana',
                'homework_status': 'Excellent',
                'behavior': 'Good',
            },
        )
        EducationRecord.objects.update_or_create(
            child=fatima,
            school_name='Govt School #5',
            grade='Class 4',
            defaults={
                'roll_number': '102',
                'attendance_percent': Decimal('87.00'),
                'urdu_marks': Decimal('82.00'),
                'english_marks': Decimal('75.00'),
                'math_marks': Decimal('88.00'),
                'science_marks': Decimal('80.00'),
                'islamiat_marks': Decimal('85.00'),
                'teacher_name': 'Miss Sana',
                'homework_status': 'Good',
                'behavior': 'Excellent',
            },
        )

        StaffMember.objects.update_or_create(
            staff_id='ST001',
            defaults={
                'full_name': 'Dr. Ayesha Khan',
                'position': 'Medical Officer',
                'department': 'Health',
                'shift': 'morning',
                'salary': Decimal('85000.00'),
                'joining_date': date(2023, 1, 15),
                'experience': '6 years',
                'qualification': 'MBBS',
                'phone': '+92 300 1234567',
                'email': 'ayesha@kafalatcare.pk',
                'status': 'active',
            },
        )
        StaffMember.objects.update_or_create(
            staff_id='ST002',
            defaults={
                'full_name': 'Muhammad Usman',
                'position': 'Senior Caretaker',
                'department': 'Operations',
                'shift': 'rotating',
                'salary': Decimal('55000.00'),
                'joining_date': date(2022, 8, 20),
                'experience': '4 years',
                'qualification': 'BA',
                'phone': '+92 300 2345678',
                'email': 'usman@kafalatcare.pk',
                'status': 'active',
            },
        )

        Sponsorship.objects.update_or_create(
            sponsor_code='SP001',
            defaults={
                'sponsor_name': 'Ahmed Malik',
                'cnic': '12345-1234567-1',
                'phone': '+92 300 1112222',
                'email': 'ahmed@example.com',
                'child': hassan,
                'monthly_amount': Decimal('3500.00'),
                'start_date': date(2026, 3, 15),
                'payment_method': 'Bank Transfer',
                'last_payment_date': date(2026, 5, 1),
                'next_payment_date': date(2026, 6, 1),
                'status': 'active',
                'ai_match_score': 95,
            },
        )
        Sponsorship.objects.update_or_create(
            sponsor_code='SP002',
            defaults={
                'sponsor_name': 'Saira Ahmed',
                'cnic': '12345-2345678-2',
                'phone': '+92 300 2223333',
                'email': 'saira@example.com',
                'child': ali,
                'monthly_amount': Decimal('4000.00'),
                'start_date': date(2026, 2, 5),
                'payment_method': 'JazzCash',
                'last_payment_date': date(2026, 5, 5),
                'next_payment_date': date(2026, 6, 5),
                'status': 'active',
                'ai_match_score': 88,
            },
        )

        Donation.objects.update_or_create(
            transaction_id='TXN123456',
            defaults={
                'donor_name': 'Abdullah Traders',
                'donor_type': 'corporate',
                'amount': Decimal('150000.00'),
                'donation_type': 'one_time',
                'payment_method': 'Bank Transfer',
                'donated_at': date(2026, 5, 15),
                'allocated_to': 'General Fund',
                'receipt_number': 'RC001',
                'tax_certificate_issued': True,
                'status': 'completed',
            },
        )
        Donation.objects.update_or_create(
            transaction_id='TXN123457',
            defaults={
                'donor_name': 'Hina Malik',
                'donor_type': 'individual',
                'amount': Decimal('25000.00'),
                'donation_type': 'monthly',
                'payment_method': 'Credit Card',
                'donated_at': date(2026, 5, 10),
                'allocated_to': 'Education Fund',
                'receipt_number': 'RC002',
                'tax_certificate_issued': True,
                'status': 'completed',
            },
        )

        self.stdout.write(self.style.SUCCESS('Dashboard demo data seeded successfully.'))
