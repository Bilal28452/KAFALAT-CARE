from django import forms
from .models import MealSchedule, MealRecord, ChildAllergy
from children.models import Child


class MealScheduleForm(forms.ModelForm):
    class Meta:
        model = MealSchedule
        fields = ['day', 'meal_type', 'food_items', 'nutritional_notes', 'is_active']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-select'}),
            'meal_type': forms.Select(attrs={'class': 'form-select'}),
            'food_items': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Paratha, Chai, Egg'}),
            'nutritional_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DailyMealLogForm(forms.Form):
    child = forms.ModelChoiceField(queryset=Child.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))


class ChildAllergyForm(forms.ModelForm):
    class Meta:
        model = ChildAllergy
        fields = ['allergies', 'dietary_restrictions', 'notes']
        widgets = {
            'allergies': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Peanuts, Milk, Eggs'}),
            'dietary_restrictions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., No beef, Vegetarian'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }