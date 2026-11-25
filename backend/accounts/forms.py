from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import AccountProfile


User = get_user_model()


class AdminSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    role = forms.ChoiceField(choices=AccountProfile.ROLE_CHOICES)
    phone = forms.CharField(max_length=30, required=False)
    cnic = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('first_name', 'username', 'email', 'role', 'phone', 'cnic', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.is_staff = self.cleaned_data['role'] == AccountProfile.ROLE_ADMIN

        if commit:
            user.save()
            AccountProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                phone=self.cleaned_data.get('phone', ''),
                cnic=self.cleaned_data.get('cnic', ''),
            )

        return user


class AdminLoginForm(forms.Form):
    email = forms.EmailField(label='Email Address')
    role = forms.ChoiceField(choices=AccountProfile.ROLE_CHOICES)
    password = forms.CharField(widget=forms.PasswordInput)
    remember = forms.BooleanField(required=False)

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        role = cleaned_data.get('role')
        password = cleaned_data.get('password')

        if not email or not role or not password:
            return cleaned_data

        users = User.objects.filter(email__iexact=email.strip())
        if not users.exists():
            raise forms.ValidationError('Invalid email or password.')

        self.user = None
        for user in users:
            authenticated = authenticate(
                self.request,
                username=user.get_username(),
                password=password,
            )
            if authenticated is not None:
                self.user = authenticated
                break

        if self.user is None:
            raise forms.ValidationError('Invalid email or password.')

        if not self.user.is_active:
            raise forms.ValidationError('This account is inactive.')

        # Auto-create AccountProfile if it doesn't exist
        if not hasattr(self.user, 'account_profile'):
            AccountProfile.objects.create(
                user=self.user,
                role=role,
            )

        if self.user.account_profile.role != role:
            raise forms.ValidationError('The selected role does not match this account.')

        return cleaned_data
