from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import PatientInformation


def is_staff(user):
    return user.is_staff


# ── Auth views ────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return _redirect_after_login(request.user)
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user:
            login(request, user)
            return _redirect_after_login(user)
        return render(request, 'login.html', {'form': {'errors': True}})
    return render(request, 'login.html', {})


def logout_view(request):
    logout(request)
    return redirect('login')


def _redirect_after_login(user):
    return redirect('dashboard')


# ── Clinician views (staff only) ──────────────────────────────────────────────

@login_required(login_url='login')
@user_passes_test(is_staff, login_url='login')
def patient_list(request):
    patients = PatientInformation.objects.order_by('last_name', 'first_name')
    return render(request, 'patient_list.html', {'patients': patients})


@login_required(login_url='login')
@user_passes_test(is_staff, login_url='login')
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
