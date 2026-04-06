from django.contrib import admin
from .models import HealthCareProvider


@admin.register(HealthCareProvider)
class HealthCareProviderAdmin(admin.ModelAdmin):
    list_display  = ('hcp_id', 'last_name', 'first_name', 'hcp_type', 'specialty', 'gender')
    list_filter   = ('hcp_type', 'specialty')
    search_fields = ('first_name', 'last_name', 'specialty')
    ordering      = ('last_name', 'first_name')
