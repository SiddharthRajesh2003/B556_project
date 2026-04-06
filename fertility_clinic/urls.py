from django.contrib import admin
from django.urls import path
from fertility_clinic.views import dashboard
from patients.views import patient_list, patient_detail
from appointments.views import appointment_list
from specimens.views import specimen_list

admin.site.site_header = "Fertility Clinic Management System"
admin.site.site_title  = "Fertility Clinic Admin"
admin.site.index_title = "Client & Donor Management"

urlpatterns = [
    path('',                      dashboard,        name='dashboard'),
    path('patients/',             patient_list,     name='patient-list'),
    path('patients/<int:pk>/',    patient_detail,   name='patient-detail'),
    path('appointments/',         appointment_list, name='appointment-list'),
    path('specimens/',            specimen_list,    name='specimen-list'),
    path('admin/',                admin.site.urls),
]
