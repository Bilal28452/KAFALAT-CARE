from django.db import models
from django.conf import settings
from django.utils import timezone
from children.models import Child
from staff_management.models import StaffMember


class MealSchedule(models.Model):
    """Weekly meal schedule template"""
    
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]
    
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES)
    food_items = models.CharField(max_length=500, help_text="Comma separated food items")
    nutritional_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['day', 'meal_type']
        ordering = ['day', 'meal_type']
    
    def __str__(self):
        return f"{self.get_day_display()} - {self.get_meal_type_display()}: {self.food_items}"


class MealRecord(models.Model):
    """Daily meal consumption record for a child"""
    
    EATING_STATUS_CHOICES = [
        ('ate_fully', 'Ate Fully'),
        ('partially_ate', 'Partially Ate'),
        ('refused', 'Refused'),
        ('absent', 'Absent/Sick'),
    ]
    
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='meal_records')
    date = models.DateField(default=timezone.localdate)
    meal_type = models.CharField(max_length=20, choices=MealSchedule.MEAL_CHOICES)
    scheduled_food = models.CharField(max_length=500, help_text="What was scheduled to be served")
    status = models.CharField(max_length=20, choices=EATING_STATUS_CHOICES)
    activity_notes = models.TextField(blank=True, help_text="Child's behavior, mood, complaints")
    recorded_by = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['child', 'date', 'meal_type']
        ordering = ['-date', 'meal_type']
    
    def __str__(self):
        return f"{self.child.full_name} - {self.date} - {self.get_meal_type_display()}: {self.get_status_display()}"


class ChildAllergy(models.Model):
    """Allergies for each child"""
    
    child = models.OneToOneField(Child, on_delete=models.CASCADE, related_name='allergies')
    allergies = models.TextField(blank=True, help_text="Comma separated list of allergies")
    dietary_restrictions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Allergies for {self.child.full_name}"
    
    def get_allergies_list(self):
        return [a.strip() for a in self.allergies.split(',') if a.strip()]