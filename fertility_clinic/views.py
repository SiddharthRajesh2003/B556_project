from django.shortcuts import render
from django.utils import timezone
from patients.models import PatientInformation
from appointments.models import Appointment
from specimens.models import SpermSpecimen, OocyteSpecimen, EmbryoInformation
from providers.models import HealthCareProvider


def dashboard(request):
    today = timezone.localdate()
    context = {
        'total_patients':       PatientInformation.objects.count(),
        'today_appointments':   Appointment.objects.filter(scheduled_date=today).count(),
        'total_specimens':      (SpermSpecimen.objects.count() +
                                 OocyteSpecimen.objects.count() +
                                 EmbryoInformation.objects.count()),
        'total_providers':      HealthCareProvider.objects.count(),
        'upcoming_appointments': Appointment.objects.filter(
            scheduled_date__gte=today
        ).select_related('patient', 'hcp').order_by('scheduled_date', 'scheduled_time')[:5],
        'recent_patients': PatientInformation.objects.order_by('-patient_id')[:5],
    }
    return render(request, 'dashboard.html', context)
