from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from fertility_clinic.views import dashboard
from patients.views import patient_list, patient_detail, login_view, logout_view
from appointments.views import appointment_list
from specimens.views import specimen_list

admin.site.site_header = "Fertility Clinic Management System"
admin.site.site_title  = "Fertility Clinic Admin"
admin.site.index_title = "Client & Donor Management"

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboard')),
    # Auth
    path('login/',                              login_view,       name='login'),
    path('logout/',                             logout_view,      name='logout'),
    # Clinician views
    path('clinical/',                           dashboard,        name='dashboard'),
    path('clinical/patients/',                  patient_list,     name='patient-list'),
    path('clinical/patients/<int:pk>/',         patient_detail,   name='patient-detail'),
    path('clinical/appointments/',              appointment_list, name='appointment-list'),
    path('clinical/specimens/',                 specimen_list,    name='specimen-list'),
    path('admin/',                              admin.site.urls),
]
