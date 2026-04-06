from django.db import models


class PatientInformation(models.Model):
    MALE   = 'Male'
    FEMALE = 'Female'
    PATIENT_TYPE_CHOICES = [(MALE, 'Male'), (FEMALE, 'Female')]

    SEX_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Intersex', 'Intersex')]

    patient_id     = models.AutoField(primary_key=True, db_column='Patient_ID')
    first_name     = models.CharField(max_length=50)
    last_name      = models.CharField(max_length=50)
    dob            = models.DateField(null=True, blank=True, verbose_name='Date of Birth')
    patient_type   = models.CharField(max_length=6, choices=PATIENT_TYPE_CHOICES)
    sex_at_birth   = models.CharField(max_length=10, choices=SEX_CHOICES, null=True, blank=True)
    patient_gender = models.CharField(max_length=30, null=True, blank=True)
    treatment_plan = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'PatientInformation'
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name}, {self.first_name} (ID: {self.pk})"


class PatientMedicalHistory(models.Model):
    patient            = models.OneToOneField(
        PatientInformation, on_delete=models.CASCADE,
        primary_key=True, db_column='Patient_ID',
        related_name='medical_history'
    )
    diabetes_status    = models.CharField(max_length=50, null=True, blank=True)
    height             = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight             = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    blood_type         = models.CharField(max_length=5, null=True, blank=True)
    medical_conditions = models.TextField(null=True, blank=True)
    surgical_history   = models.TextField(null=True, blank=True)
    alcohol_use        = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'PatientMedicalHistory'
        verbose_name = 'Medical History'
        verbose_name_plural = 'Medical Histories'

    def __str__(self):
        return f"Medical History — {self.patient}"


class FemalePatients(models.Model):
    patient                  = models.OneToOneField(
        PatientInformation, on_delete=models.CASCADE,
        primary_key=True, db_column='Patient_ID',
        related_name='female_data'
    )
    cycle_number             = models.IntegerField(null=True, blank=True)
    length_of_cycle          = models.IntegerField(null=True, blank=True)
    mean_cycle_length        = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    estimated_day_of_ovulation = models.IntegerField(null=True, blank=True)
    reproductive_category    = models.IntegerField(null=True, blank=True,
                                   help_text='0 = normal; see study coding for other values')
    total_days_of_fertility  = models.IntegerField(null=True, blank=True)
    mean_menses_length       = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_menses_score       = models.IntegerField(null=True, blank=True)
    unusual_bleeding         = models.BooleanField(null=True, blank=True)
    numberpreg               = models.IntegerField(null=True, blank=True, verbose_name='Number of pregnancies')
    livingkids               = models.IntegerField(null=True, blank=True, verbose_name='Living children')
    miscarriages             = models.IntegerField(null=True, blank=True)
    abortions                = models.IntegerField(null=True, blank=True)
    breastfeeding            = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = 'FemalePatients'
        verbose_name = 'Female Patient Record'
        verbose_name_plural = 'Female Patient Records'

    def __str__(self):
        return f"Female Record — {self.patient}"


class MalePatients(models.Model):
    patient               = models.OneToOneField(
        PatientInformation, on_delete=models.CASCADE,
        primary_key=True, db_column='Patient_ID',
        related_name='male_data'
    )
    trauma_history        = models.BooleanField(null=True, blank=True)
    fever_history         = models.CharField(max_length=50, null=True, blank=True)
    activity_levels       = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                help_text='Hours spent sitting per day')
    diagnosis             = models.CharField(max_length=20, null=True, blank=True,
                                help_text='Normal or Altered')

    class Meta:
        db_table = 'MalePatients'
        verbose_name = 'Male Patient Record'
        verbose_name_plural = 'Male Patient Records'

    def __str__(self):
        return f"Male Record — {self.patient}"
