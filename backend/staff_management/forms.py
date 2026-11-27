from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from children.models import Attendance, Child, Course, EducationResult
from meals.models import MealRecord

from .models import CareIncident, DailyCareLog, StaffMember

User = get_user_model()


class TeacherAttendanceForm(forms.Form):
    date = forms.DateField(widget=forms.HiddenInput)

    def __init__(self, *args, education_records, attendance_by_child=None, **kwargs):
        super().__init__(*args, **kwargs)
        attendance_by_child = attendance_by_child or {}

        for record in education_records:
            field_name = f'status_{record.child_id}'
            self.fields[field_name] = forms.ChoiceField(
                choices=[('', 'Select status'), *Attendance.STATUS_CHOICES],
                required=True,
                widget=forms.Select(attrs={'class': 'form-select'}),
                label='Attendance status',
            )
            attendance = attendance_by_child.get(record.child_id)
            if attendance:
                self.initial[field_name] = attendance.status

    def clean_date(self):
        attendance_date = self.cleaned_data['date']
        if attendance_date > timezone.localdate():
            raise forms.ValidationError('Attendance cannot be marked for a future date.')
        return attendance_date


class CaretakerMealLogForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'form-control',
    }))

    def __init__(self, *args, schedules, records_by_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        records_by_type = records_by_type or {}
        status_choices = [('', 'Select status'), *MealRecord.EATING_STATUS_CHOICES]

        for schedule in schedules:
            meal_type = schedule.meal_type
            self.fields[f'status_{meal_type}'] = forms.ChoiceField(
                choices=status_choices,
                required=True,
                label=f'{schedule.get_meal_type_display()} status',
                widget=forms.Select(attrs={'class': 'form-select'}),
            )
            self.fields[f'notes_{meal_type}'] = forms.CharField(
                required=False,
                label=f'{schedule.get_meal_type_display()} notes',
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Optional observations',
                }),
            )
            existing_record = records_by_type.get(meal_type)
            if existing_record:
                self.initial[f'status_{meal_type}'] = existing_record.status
                self.initial[f'notes_{meal_type}'] = existing_record.activity_notes

    def clean_date(self):
        meal_date = self.cleaned_data['date']
        if meal_date > timezone.localdate():
            raise forms.ValidationError('Meal records cannot be entered for a future date.')
        return meal_date


class CaretakerDailyCareForm(forms.ModelForm):
    class Meta:
        model = DailyCareLog
        fields = [
            'date', 'hygiene_status', 'rest_status', 'mood', 'notes', 'handover_notes',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hygiene_status': forms.Select(attrs={'class': 'form-select'}),
            'rest_status': forms.Select(attrs={'class': 'form-select'}),
            'mood': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'handover_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date(self):
        care_date = self.cleaned_data['date']
        if care_date > timezone.localdate():
            raise forms.ValidationError('Care logs cannot be entered for a future date.')
        return care_date


class CaretakerIncidentForm(forms.ModelForm):
    class Meta:
        model = CareIncident
        fields = ['category', 'severity', 'description', 'immediate_action']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'immediate_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DoctorIncidentReviewForm(forms.ModelForm):
    class Meta:
        model = CareIncident
        fields = ['status', 'review_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'review_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class TeacherEducationResultForm(forms.ModelForm):
    class Meta:
        model = EducationResult
        fields = ['child', 'course', 'term', 'score', 'remarks']
        widgets = {
            'child': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'term': forms.Select(attrs={'class': 'form-select'}),
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
            }),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, staff_member, **kwargs):
        self.staff_member = staff_member
        super().__init__(*args, **kwargs)
        self.fields['child'].queryset = Child.objects.filter(
            education_record__class_teacher=staff_member,
        ).order_by('full_name')
        self.fields['course'].queryset = Course.objects.order_by('code')

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score is not None and not 0 <= score <= 100:
            raise forms.ValidationError('Enter a score between 0 and 100.')
        return score

    def save(self, commit=True):
        result = super().save(commit=False)
        result.teacher = self.staff_member
        if commit:
            result.save()
        return result


class StaffMemberForm(forms.ModelForm):
    """Form for creating and updating Staff Member records"""
    
    class Meta:
        model = StaffMember
        fields = [
            'user', 'staff_id', 'position', 'department', 'shift',
            'salary', 'joining_date', 'experience', 'qualification', 'employment_status'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'staff_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., ST001'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Caregiver, Teacher, Manager'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Child Care, Education, Administration'
            }),
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monthly salary in PKR',
                'min': '0',
                'step': '0.01'
            }),
            'joining_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'experience': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5 years in child care'
            }),
            'qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Bachelor in Education'
            }),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'user': 'Select Staff User',
            'staff_id': 'Staff ID',
            'position': 'Position',
            'department': 'Department',
            'shift': 'Shift',
            'salary': 'Monthly Salary (PKR)',
            'joining_date': 'Joining Date',
            'experience': 'Experience',
            'qualification': 'Qualification',
            'employment_status': 'Employment Status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing_staff_users = StaffMember.objects.filter(user__isnull=False).values_list('user_id', flat=True)
        self.fields['user'].queryset = User.objects.filter(
            is_active=True,
            account_profile__role='staff'
        ).exclude(id__in=existing_staff_users)
        self.fields['user'].empty_label = "Select a staff user..."
        self.fields['user'].label = "Select Staff User (Only users with Staff role)"

    def clean_staff_id(self):
        staff_id = self.cleaned_data.get('staff_id')
        if staff_id:
            staff_id = staff_id.strip().upper()
            if self.instance.pk:
                if StaffMember.objects.exclude(pk=self.instance.pk).filter(staff_id=staff_id).exists():
                    raise forms.ValidationError('A staff member with this ID already exists.')
            else:
                if StaffMember.objects.filter(staff_id=staff_id).exists():
                    raise forms.ValidationError('A staff member with this ID already exists.')
        return staff_id

    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        if salary and salary < 0:
            raise forms.ValidationError('Salary cannot be negative.')
        return salary