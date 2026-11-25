from django import forms
from django.contrib.auth import get_user_model
from .models import StaffMember

User = get_user_model()


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