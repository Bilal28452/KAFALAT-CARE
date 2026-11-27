from django.contrib import admin

from .models import Child, EducationRecord, HealthRecord, Course, EducationResult


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('child_id', 'full_name', 'gender', 'health_status', 'sponsor_status', 'admission_date')
    list_filter = ('gender', 'health_status', 'sponsor_status', 'admission_date')
    search_fields = ('child_id', 'full_name', 'emergency_contact')
    filter_horizontal = ('doctors', 'caretakers')


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ('child', 'record_type', 'last_checkup', 'next_checkup', 'vaccinations', 'status', 'doctor_name')
    list_filter = ('vaccinations', 'status', 'record_type', 'last_checkup')
    search_fields = ('child__full_name', 'doctor_name', 'current_medications', 'allergies')


@admin.register(EducationRecord)
class EducationRecordAdmin(admin.ModelAdmin):
    list_display = ('child', 'grade_level', 'roll_number', 'get_class_teacher', 'academic_year', 'admission_date_to_school')
    list_filter = ('grade_level', 'academic_year')
    search_fields = ('child__full_name', 'roll_number')
    
    def get_class_teacher(self, obj):
        if obj.class_teacher:
            return obj.class_teacher.user.get_full_name() if obj.class_teacher.user else obj.class_teacher.staff_id
        return '-'
    get_class_teacher.short_description = 'Class Teacher'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'created_at')
    search_fields = ('code', 'title')


@admin.register(EducationResult)
class EducationResultAdmin(admin.ModelAdmin):
    list_display = ('child', 'course', 'get_teacher', 'term', 'score', 'grade', 'created_at')
    list_filter = ('term', 'course')
    search_fields = ('child__full_name', 'course__title')
    
    def get_teacher(self, obj):
        if obj.teacher:
            return obj.teacher.user.get_full_name() if obj.teacher.user else obj.teacher.staff_id
        return '-'
    get_teacher.short_description = 'Teacher'