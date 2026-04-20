from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Appointment


def is_staff(user):
    return user.is_staff


@login_required(login_url='login')
@user_passes_test(is_staff, login_url='login')
def appointment_list(request):
    appointments = Appointment.objects.select_related(
        'patient', 'hcp'
    ).order_by('-scheduled_date', 'scheduled_time')
    return render(request, 'appointment_list.html', {'appointments': appointments})
