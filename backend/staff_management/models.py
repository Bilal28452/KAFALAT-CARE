from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class StaffMember(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('probation', 'Probation'),
        ('inactive', 'Inactive'),
    ]
    SHIFT_CHOICES = [
        ('morning', 'Morning'),
        ('evening', 'Evening'),
        ('night', 'Night'),
        ('rotating', 'Rotating'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    staff_id = models.CharField(max_length=30, unique=True)
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='morning')
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    joining_date = models.DateField(default=timezone.localdate)
    experience = models.CharField(max_length=80, blank=True)
    qualification = models.CharField(max_length=120, blank=True)
    employment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['staff_id']

    def __str__(self):
        return f'{self.staff_id} - {self.user.get_full_name() if self.user else "No User"}'


class StaffAttendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('leave', 'On Leave'),
        ('half_day', 'Half Day'),
    ]
    
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['staff', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.staff.staff_id} - {self.date} - {self.get_status_display()}"


class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('annual', 'Annual Leave'),
        ('emergency', 'Emergency Leave'),
        ('unpaid', 'Unpaid Leave'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.staff.staff_id} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"
    
    @property
    def days_count(self):
        delta = self.end_date - self.start_date
        return delta.days + 1


class SalaryRecord(models.Model):
    PAYMENT_STATUS = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
    ]
    
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='salaries')
    month = models.IntegerField()
    year = models.IntegerField()
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    attendance_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['staff', 'month', 'year']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.staff.staff_id} - {self.month}/{self.year}"
    
    def save(self, *args, **kwargs):
        # Convert to Decimal if they are strings
        base = Decimal(str(self.base_salary)) if self.base_salary else Decimal('0')
        bonus = Decimal(str(self.attendance_bonus)) if self.attendance_bonus else Decimal('0')
        overtime = Decimal(str(self.overtime_pay)) if self.overtime_pay else Decimal('0')
        deductions = Decimal(str(self.deductions)) if self.deductions else Decimal('0')
        advances = Decimal(str(self.advances)) if self.advances else Decimal('0')
        
        self.net_salary = base + bonus + overtime - deductions - advances
        super().save(*args, **kwargs)