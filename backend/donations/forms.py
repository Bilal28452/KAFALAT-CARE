from django import forms
from .models import Donation


class DonationForm(forms.ModelForm):
    """Form for creating and updating Donation records"""
    
    class Meta:
        model = Donation
        fields = [
            'donor_name', 'donor_type', 'amount', 'donation_type',
            'payment_method', 'transaction_id', 'donated_at',
            'allocated_to', 'receipt_number', 'tax_certificate_issued', 'status'
        ]
        widgets = {
            'donor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Donor full name'
            }),
            'donor_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Amount in PKR',
                'min': '0',
                'step': '0.01'
            }),
            'donation_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_method': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Bank Transfer, JazzCash, EasyPaisa'
            }),
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Transaction/Reference ID'
            }),
            'donated_at': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'allocated_to': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Food, Education, Medical'
            }),
            'receipt_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Receipt number'
            }),
            'tax_certificate_issued': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'donor_name': 'Donor Name',
            'donor_type': 'Donor Type',
            'amount': 'Amount (PKR)',
            'donation_type': 'Donation Type',
            'payment_method': 'Payment Method',
            'transaction_id': 'Transaction ID',
            'donated_at': 'Donation Date',
            'allocated_to': 'Allocated To',
            'receipt_number': 'Receipt Number',
            'tax_certificate_issued': 'Tax Certificate Issued',
            'status': 'Status',
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount


class DonorDonationForm(forms.ModelForm):
    """Donation submission form for authenticated donor users."""

    class Meta:
        model = Donation
        fields = [
            'donor_type', 'amount', 'donation_type', 'payment_method',
            'transaction_id', 'donated_at', 'allocated_to'
        ]
        widgets = {
            'donor_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount in PKR', 'min': '1', 'step': '0.01'}),
            'donation_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bank Transfer, JazzCash, EasyPaisa'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transaction / Reference ID'}),
            'donated_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'allocated_to': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Food, Education, Medical'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount
