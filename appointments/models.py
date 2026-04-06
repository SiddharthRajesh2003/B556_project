from django.db import models
from patients.models import PatientInformation
from providers.models import HealthCareProvider


class Appointment(models.Model):
    appointment_id = models.AutoField(primary_key=True, db_column='Appointment_ID')
    patient        = models.ForeignKey(PatientInformation, on_delete=models.CASCADE,
                         db_column='Patient_ID', related_name='appointments')
    hcp            = models.ForeignKey(HealthCareProvider, on_delete=models.RESTRICT,
                         db_column='HCP_ID', related_name='appointments',
                         verbose_name='Health Care Provider')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(null=True, blank=True)
    duration       = models.IntegerField(null=True, blank=True, help_text='Duration in minutes')
    room_number    = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'Appointments'
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        ordering = ['-scheduled_date', 'scheduled_time']

    def __str__(self):
        return f"{self.patient} — {self.scheduled_date} with {self.hcp}"


class Result(models.Model):
    result_id      = models.AutoField(primary_key=True, db_column='Result_ID')
    appointment    = models.ForeignKey(Appointment, on_delete=models.CASCADE,
                         db_column='Appointment_ID', related_name='results')
    procedure_name = models.CharField(max_length=100, null=True, blank=True)
    type           = models.CharField(max_length=50, null=True, blank=True)
    result         = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'Results'
        verbose_name = 'Result'
        verbose_name_plural = 'Results'

    def __str__(self):
        return f"{self.procedure_name} — {self.appointment.scheduled_date}"
