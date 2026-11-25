from django import forms
from .models import Child, HealthRecord, EducationRecord, Course, EducationResult


class ChildForm(forms.ModelForm):
    """Form for creating and updating Child records"""
    
    class Meta:
        model = Child
        fields = [
            'child_id', 'full_name', 'photo', 'date_of_birth', 'gender',
            'health_status', 'education_level', 'sponsor_status',
            'emergency_contact', 'admission_date'
        ]
        widgets = {
            'child_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CH001'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'health_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'education_level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Grade 5'
            }),
            'sponsor_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact number'
            }),
            'admission_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'child_id': 'Child ID',
            'full_name': 'Full Name',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'health_status': 'Health Status',
            'education_level': 'Education Level',
            'sponsor_status': 'Sponsorship Status',
            'emergency_contact': 'Emergency Contact',
            'admission_date': 'Admission Date',
        }

    def clean_child_id(self):
        child_id = self.cleaned_data.get('child_id')
        if child_id:
            child_id = child_id.strip().upper()
            if self.instance.pk:
                if Child.objects.exclude(pk=self.instance.pk).filter(child_id=child_id).exists():
                    raise forms.ValidationError('A child with this ID already exists.')
            else:
                if Child.objects.filter(child_id=child_id).exists():
                    raise forms.ValidationError('A child with this ID already exists.')
        return child_id


class HealthRecordForm(forms.ModelForm):
    """Form for creating and updating Health Records"""

    def clean_temperature_c(self):
        temperature = self.cleaned_data.get('temperature_c')
        if temperature is not None and not 30 <= temperature <= 45:
            raise forms.ValidationError('Enter a temperature between 30 and 45 °C.')
        return temperature
    
    class Meta:
        model = HealthRecord
        fields = [
            'child', 'record_type', 'last_checkup', 'next_checkup', 'doctor_name',
            'symptoms', 'diagnosis', 'blood_type', 'weight', 'height',
            'temperature_c',
            'vaccinations', 'current_medications', 'allergies', 'treatment_plan',
            'medical_history', 'status', 'priority_level', 'follow_up_due',
            'follow_up_status', 'notes_for_guardian'
        ]
        widgets = {
            'child': forms.Select(attrs={
                'class': 'form-select'
            }),
            'record_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'last_checkup': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'next_checkup': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'doctor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Doctor's name"
            }),
            'blood_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., A+, B-, O+'
            }),
            'weight': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 35 kg'
            }),
            'temperature_c': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 37.0',
                'min': '30',
                'max': '45',
                'step': '0.1'
            }),
            'height': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 140 cm'
            }),
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe symptoms or chief complaint'
            }),
            'diagnosis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': "Doctor's diagnosis"
            }),
            'vaccinations': forms.Select(attrs={
                'class': 'form-select'
            }),
            'current_medications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List current medications'
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List any allergies'
            }),
            'treatment_plan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recommended treatment plan'
            }),
            'medical_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Relevant medical history'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'follow_up_due': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'follow_up_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes_for_guardian': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notes to share with guardian/parent'
            }),
        }
        labels = {
            'child': 'Select Child',
            'record_type': 'Record Type',
            'last_checkup': 'Checkup Date',
            'next_checkup': 'Next Checkup Date',
            'doctor_name': 'Doctor Name',
            'blood_type': 'Blood Type',
            'weight': 'Weight',
            'temperature_c': 'Temperature (°C)',
            'height': 'Height',
            'symptoms': 'Chief Complaint/Symptoms',
            'diagnosis': 'Diagnosis',
            'vaccinations': 'Vaccination Status',
            'current_medications': 'Current Medications',
            'allergies': 'Allergies',
            'treatment_plan': 'Treatment Plan',
            'medical_history': 'Medical History',
            'status': 'Health Status',
            'priority_level': 'Priority Level',
            'follow_up_due': 'Follow-up Due Date',
            'follow_up_status': 'Follow-up Status',
            'notes_for_guardian': 'Notes for Guardian',
        }


class EducationRecordForm(forms.ModelForm):
    """Form for basic education information - ONE record per child"""
    
    class Meta:
        model = EducationRecord
        fields = [
            'child',
            'grade_level',
            'roll_number',
            'class_teacher',
            'admission_date_to_school',
            'academic_year',
        ]
        widgets = {
            'child': forms.Select(attrs={
                'class': 'form-select'
            }),
            'grade_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'roll_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 101'
            }),
            'class_teacher': forms.Select(attrs={
                'class': 'form-select'
            }),
            'admission_date_to_school': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'child': 'Child',
            'grade_level': 'Grade Level',
            'roll_number': 'Roll Number',
            'class_teacher': 'Class Teacher',
            'admission_date_to_school': 'Admission Date',
            'academic_year': 'Academic Year',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show staff members who are teachers
        from staff_management.models import StaffMember
        self.fields['class_teacher'].queryset = StaffMember.objects.filter(
            position__icontains='Teacher'
        )
        # Add empty label
        self.fields['class_teacher'].empty_label = "Select a teacher"


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'code', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course title'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course code'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Course description'}),
        }
        labels = {
            'title': 'Course Title',
            'code': 'Course Code',
            'description': 'Description',
        }


# TeacherForm is REMOVED because Teacher is now handled by StaffMember model


class EducationResultForm(forms.ModelForm):
    class Meta:
        model = EducationResult
        fields = ['child', 'course', 'teacher', 'term', 'score', 'remarks']
        widgets = {
            'child': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'term': forms.Select(attrs={'class': 'form-select'}),
            'score': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '0-100', 
                'min': '0', 
                'max': '100', 
                'step': '0.01'
            }),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional remarks'}),
        }
        labels = {
            'child': 'Child',
            'course': 'Course',
            'teacher': 'Teacher (Staff Member)',
            'term': 'Term',
            'score': 'Score (0-100)',
            'remarks': 'Remarks',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show staff members who are teachers
        from staff_management.models import StaffMember
        self.fields['teacher'].queryset = StaffMember.objects.filter(
            position__icontains='Teacher'
        )
        self.fields['teacher'].empty_label = "Select a teacher"

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score is not None and (score < 0 or score > 100):
            raise forms.ValidationError('Enter a score between 0 and 100.')
        return score