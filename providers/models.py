from django.db import models


class HealthCareProvider(models.Model):
    hcp_id     = models.AutoField(primary_key=True, db_column='HCP_ID')
    hcp_type   = models.CharField(max_length=50, null=True, blank=True, db_column='HCP_Type', verbose_name='Provider Type')
    first_name = models.CharField(max_length=50, db_column='First_Name')
    last_name  = models.CharField(max_length=50, db_column='Last_Name')
    specialty  = models.CharField(max_length=100, null=True, blank=True, db_column='Specialty')
    gender     = models.CharField(max_length=20, null=True, blank=True, db_column='Gender')

    class Meta:
        db_table = 'HealthCareProvider'
        verbose_name = 'Health Care Provider'
        verbose_name_plural = 'Health Care Providers'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"Dr. {self.last_name}, {self.first_name} ({self.specialty or self.hcp_type})"
