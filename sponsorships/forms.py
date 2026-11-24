from django import forms
from .models import Sponsorship
from children.models import Child


class SponsorshipForm(forms.ModelForm):
    """Form for creating and updating Sponsorship records"""
    
    class Meta:
        model = Sponsorship
        fields = [
            'sponsor_code', 'sponsor_name', 'cnic', 'phone', 'email',
            'child', 'monthly_amount', 'start_date', 'payment_method',
            'last_payment_date', 'next_payment_date', 'status', 'ai_match_score'
        ]
        widgets = {
            'sponsor_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., SP001'
            }),
            'sponsor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sponsor full name'
            }),
            'cnic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CNIC (e.g., 12345-1234567-1)'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            }),
            'child': forms.Select(attrs={
                'class': 'form-select'
            }),
            'monthly_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monthly amount in PKR',
                'min': '0',
                'step': '0.01'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_method': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Bank Transfer, JazzCash'
            }),
            'last_payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'next_payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ai_match_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'AI Match Score (0-100)',
                'min': '0',
                'max': '100'
            }),
        }
        labels = {
            'sponsor_code': 'Sponsor Code',
            'sponsor_name': 'Sponsor Name',
            'cnic': 'CNIC',
            'phone': 'Phone Number',
            'email': 'Email Address',
            'child': 'Sponsored Child',
            'monthly_amount': 'Monthly Amount (PKR)',
            'start_date': 'Start Date',
            'payment_method': 'Payment Method',
            'last_payment_date': 'Last Payment Date',
            'next_payment_date': 'Next Payment Date',
            'status': 'Status',
            'ai_match_score': 'AI Match Score',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter children to show only available ones (unless editing existing sponsorship)
        if not self.instance.pk:
            self.fields['child'].queryset = Child.objects.filter(sponsor_status='available')
        else:
            # When editing, show all children but mark current child
            self.fields['child'].queryset = Child.objects.all()

    def clean_sponsor_code(self):
        sponsor_code = self.cleaned_data.get('sponsor_code')
        if sponsor_code:
            sponsor_code = sponsor_code.strip().upper()
            # Check for duplicate only if creating new or changing code
            if self.instance.pk:
                if Sponsorship.objects.exclude(pk=self.instance.pk).filter(sponsor_code=sponsor_code).exists():
                    raise forms.ValidationError('A sponsorship with this code already exists.')
            else:
                if Sponsorship.objects.filter(sponsor_code=sponsor_code).exists():
                    raise forms.ValidationError('A sponsorship with this code already exists.')
        return sponsor_code

    def clean_monthly_amount(self):
        amount = self.cleaned_data.get('monthly_amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Monthly amount must be greater than zero.')
        return amount

    def clean_child(self):
        child = self.cleaned_data.get('child')
        if child:
            # Check if child is already sponsored (unless this is the current sponsorship)
            if self.instance.pk:
                # Editing existing sponsorship
                if child.sponsor_status == 'sponsored' and child != self.instance.child:
                    raise forms.ValidationError('This child is already sponsored by someone else.')
            else:
                # Creating new sponsorship
                if child.sponsor_status == 'sponsored':
                    raise forms.ValidationError('This child is already sponsored.')
        return child
