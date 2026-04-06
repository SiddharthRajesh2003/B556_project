from django.shortcuts import render, get_object_or_404
from .models import PatientInformation


def patient_list(request):
    patients = PatientInformation.objects.order_by('last_name', 'first_name')
    return render(request, 'patient_list.html', {'patients': patients})


def patient_detail(request, pk):
    patient = get_object_or_404(
        PatientInformation.objects.select_related(
            'medical_history', 'female_data', 'male_data'
        ).prefetch_related(
            'appointments__hcp', 'appointments__results',
            'sperm_specimens', 'oocyte_specimens', 'embryos'
        ),
        pk=pk
    )
    return render(request, 'patient_detail.html', {'patient': patient})
