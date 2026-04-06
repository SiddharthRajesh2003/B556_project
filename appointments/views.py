from django.shortcuts import render
from .models import Appointment


def appointment_list(request):
    appointments = Appointment.objects.select_related(
        'patient', 'hcp'
    ).order_by('-scheduled_date', 'scheduled_time')
    return render(request, 'appointment_list.html', {'appointments': appointments})
