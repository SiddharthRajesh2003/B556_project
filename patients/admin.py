from django.contrib import admin
from .models import PatientInformation, PatientMedicalHistory, FemalePatients, MalePatients


class MedicalHistoryInline(admin.StackedInline):
    model = PatientMedicalHistory
    can_delete = False
    verbose_name_plural = 'Medical History'


class FemaleDataInline(admin.StackedInline):
    model = FemalePatients
    can_delete = False
    verbose_name_plural = 'Reproductive Data (Female)'


class MaleDataInline(admin.StackedInline):
    model = MalePatients
    can_delete = False
    verbose_name_plural = 'Clinical Data (Male)'


@admin.register(PatientInformation)
class PatientInformationAdmin(admin.ModelAdmin):
    list_display  = ('patient_id', 'last_name', 'first_name', 'dob', 'patient_type', 'sex_at_birth')
    list_filter   = ('patient_type', 'sex_at_birth')
    search_fields = ('first_name', 'last_name')
    ordering      = ('last_name', 'first_name')
    inlines       = [MedicalHistoryInline, FemaleDataInline, MaleDataInline]

    fieldsets = (
        ('Demographics', {
            'fields': ('first_name', 'last_name', 'dob')
        }),
        ('Identity', {
            'fields': ('patient_type', 'sex_at_birth', 'patient_gender')
        }),
        ('Treatment', {
            'fields': ('treatment_plan',)
        }),
    )
