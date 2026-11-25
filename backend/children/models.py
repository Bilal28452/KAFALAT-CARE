from django.db import models
from django.utils import timezone


class Child(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    HEALTH_CHOICES = [
        ('healthy', 'Healthy'),
        ('under_care', 'Under Care'),
        ('medical_care', 'Medical Care'),
        ('observation', 'Under Observation'),
    ]
    SPONSOR_STATUS_CHOICES = [
        ('available', 'Available'),
        ('sponsored', 'Sponsored'),
    ]

    child_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=120)
    photo = models.ImageField(upload_to='children/photos/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=12, choices=GENDER_CHOICES, blank=True)
    health_status = models.CharField(max_length=20, choices=HEALTH_CHOICES, default='healthy')
    education_level = models.CharField(max_length=80, blank=True)
    sponsor_status = models.CharField(max_length=20, choices=SPONSOR_STATUS_CHOICES, default='available')
    emergency_contact = models.CharField(max_length=40, blank=True)
    admission_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['child_id']

    def __str__(self):
        return f'{self.child_id} - {self.full_name}'

    @property
    def age(self):
        if not self.date_of_birth:
            return ''
        today = timezone.localdate()
        years = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            years -= 1
        return f'{years} years'


class HealthRecord(models.Model):
    STATUS_CHOICES = Child.HEALTH_CHOICES
    VACCINATION_CHOICES = [
        ('complete', 'Complete'),
        ('partial', 'Partial'),
        ('pending', 'Pending'),
    ]
    RECORD_TYPE_CHOICES = [
        ('checkup', 'Regular Checkup'),
        ('vaccination', 'Vaccination'),
        ('illness', 'Illness/Injury'),
        ('emergency', 'Emergency Care'),
        ('followup', 'Follow-up'),
        ('lab', 'Lab Test'),
    ]
    PRIORITY_CHOICES = [
        ('routine', 'Routine'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    FOLLOWUP_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='health_records')
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES, default='checkup')
    last_checkup = models.DateField()
    next_checkup = models.DateField(null=True, blank=True)
    blood_type = models.CharField(max_length=5, blank=True)
    weight = models.CharField(max_length=20, blank=True)
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    height = models.CharField(max_length=20, blank=True)
    vaccinations = models.CharField(max_length=20, choices=VACCINATION_CHOICES, default='pending')
    current_medications = models.CharField(max_length=180, blank=True)
    allergies = models.CharField(max_length=180, blank=True)
    medical_history = models.TextField(blank=True)
    doctor_name = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='healthy')
    visit_number = models.IntegerField(default=1)
    linked_record = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='followup_records')
    priority_level = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='routine')
    follow_up_status = models.CharField(max_length=20, choices=FOLLOWUP_STATUS_CHOICES, default='pending')
    follow_up_due = models.DateField(null=True, blank=True)
    symptoms = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    notes_for_guardian = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_checkup']
        verbose_name_plural = 'Health Records'

    def __str__(self):
        return f'{self.child.full_name} - {self.get_record_type_display()} - {self.last_checkup}'
    
    @property
    def is_followup_overdue(self):
        """Check if follow-up is overdue"""
        if self.follow_up_due and self.follow_up_status == 'pending':
            return self.follow_up_due < timezone.localdate()
        return False


class EducationRecord(models.Model):
    """Basic education information - ONE record per child"""
    
    GRADE_LEVEL_CHOICES = [
        ('class_1', 'Class 1'),
        ('class_2', 'Class 2'),
        ('class_3', 'Class 3'),
        ('class_4', 'Class 4'),
        ('class_5', 'Class 5'),
        ('class_6', 'Class 6'),
        ('class_7', 'Class 7'),
        ('class_8', 'Class 8'),
        ('class_9', 'Class 9'),
        ('class_10', 'Class 10'),
    ]
    
    ACADEMIC_YEAR_CHOICES = [
        ('2023-2024', '2023-2024'),
        ('2024-2025', '2024-2025'),
        ('2025-2026', '2025-2026'),
        ('2026-2027', '2026-2027'),
    ]

    attendance_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Attendance percentage 0-100")
    child = models.OneToOneField(Child, on_delete=models.CASCADE, related_name='education_record')
    grade_level = models.CharField(max_length=20, choices=GRADE_LEVEL_CHOICES, blank=True)
    roll_number = models.CharField(max_length=40, blank=True)
    # Link to StaffMember (who has position = 'Teacher')
    class_teacher = models.ForeignKey(
        'staff_management.StaffMember', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='class_children'
    )
    admission_date_to_school = models.DateField(null=True, blank=True)
    academic_year = models.CharField(max_length=20, choices=ACADEMIC_YEAR_CHOICES, default='2025-2026')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['child__child_id']
        verbose_name = 'Education Record'
        verbose_name_plural = 'Education Records'

    def __str__(self):
        return f'{self.child.full_name} - {self.get_grade_level_display() or "Grade not set"}'


class Course(models.Model):
    """Courses/Subjects taught at KafalatCare School"""
    
    title = models.CharField(max_length=140)
    code = models.CharField(max_length=40, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.title}'


class EducationResult(models.Model):
    """Marks/Grades per child per course per term"""
    
    TERM_CHOICES = [
        ('term_1', 'Term 1'),
        ('term_2', 'Term 2'),
        ('term_3', 'Term 3'),
        ('final', 'Final Examination'),
        ('mid_term', 'Mid Term'),
    ]
    
    GRADE_CHOICES = [
        ('A+', 'A+ (90-100%)'),
        ('A', 'A (80-89%)'),
        ('B+', 'B+ (75-79%)'),
        ('B', 'B (70-74%)'),
        ('C', 'C (60-69%)'),
        ('D', 'D (50-59%)'),
        ('F', 'F (Below 50%)'),
    ]

    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='education_results')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='results')
    # Link to StaffMember (who has position = 'Teacher')
    teacher = models.ForeignKey(
        'staff_management.StaffMember', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='education_results'
    )
    term = models.CharField(max_length=80, choices=TERM_CHOICES, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Marks percentage (0-100)')
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, blank=True)
    remarks = models.TextField(blank=True, help_text='Additional comments about performance')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Education Result'
        verbose_name_plural = 'Education Results'

    def __str__(self):
        subject = self.course.title if self.course else 'Course'
        return f'{self.child.full_name} - {subject} ({self.get_term_display() or "Result"})'
    
    def save(self, *args, **kwargs):
        # Auto-assign grade based on score
        if self.score is not None:
            if self.score >= 90:
                self.grade = 'A+'
            elif self.score >= 80:
                self.grade = 'A'
            elif self.score >= 75:
                self.grade = 'B+'
            elif self.score >= 70:
                self.grade = 'B'
            elif self.score >= 60:
                self.grade = 'C'
            elif self.score >= 50:
                self.grade = 'D'
            else:
                self.grade = 'F'
        super().save(*args, **kwargs)


class Attendance(models.Model):
    """Daily attendance tracking for children"""
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('leave', 'Leave'),
    ]

    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    remarks = models.TextField(blank=True)
    marked_by = models.CharField(max_length=120, blank=True, help_text='Staff member who marked attendance')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['child', 'date']  # One record per child per day

    def __str__(self):
        return f'{self.child.full_name} - {self.date} - {self.get_status_display()}'