from django.contrib import admin
from .models import Appointment, Result


class ResultInline(admin.TabularInline):
    model = Result
    extra = 1


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ('appointment_id', 'patient', 'hcp', 'scheduled_date', 'scheduled_time', 'room_number')
    list_filter   = ('scheduled_date', 'hcp')
    search_fields = ('patient__first_name', 'patient__last_name', 'hcp__last_name')
    ordering      = ('-scheduled_date',)
    inlines       = [ResultInline]

    fieldsets = (
        ('Patient & Provider', {
            'fields': ('patient', 'hcp')
        }),
        ('Schedule', {
            'fields': ('scheduled_date', 'scheduled_time', 'duration', 'room_number')
        }),
    )


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display  = ('result_id', 'appointment', 'procedure_name', 'type')
    list_filter   = ('type',)
    search_fields = ('procedure_name', 'appointment__patient__last_name')
