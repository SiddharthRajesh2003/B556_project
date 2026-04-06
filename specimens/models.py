from django.db import models
from patients.models import PatientInformation


class SampleInventory(models.Model):
    storage_id          = models.AutoField(primary_key=True, db_column='Storage_ID')
    storage_temperature = models.DecimalField(max_digits=6, decimal_places=2,
                              null=True, blank=True, db_column='Storage_Temperature',
                              help_text='Temperature in Celsius')

    class Meta:
        db_table = 'SampleInventory'
        verbose_name = 'Storage Slot'
        verbose_name_plural = 'Sample Inventory'

    def __str__(self):
        return f"Storage #{self.pk} ({self.storage_temperature}°C)"


class SpermSpecimen(models.Model):
    barcode                 = models.CharField(max_length=50, primary_key=True)
    patient                 = models.ForeignKey(PatientInformation, on_delete=models.CASCADE,
                                  db_column='Patient_ID', related_name='sperm_specimens')
    storage                 = models.ForeignKey(SampleInventory, on_delete=models.SET_NULL,
                                  null=True, blank=True, db_column='Storage_ID',
                                  related_name='sperm_specimens')
    collection_date         = models.DateField(null=True, blank=True, db_column='Collection_Date')
    sperm_concentration     = models.DecimalField(max_digits=10, decimal_places=2,
                                  null=True, blank=True, db_column='Sperm_Concentration', help_text='million/mL')
    total_sperm_count       = models.DecimalField(max_digits=10, decimal_places=2,
                                  null=True, blank=True, db_column='Total_Sperm_Count', help_text='million')
    ejaculate_volume        = models.DecimalField(max_digits=5, decimal_places=2,
                                  null=True, blank=True, db_column='Ejaculate_Volume', help_text='mL')
    sperm_vitality          = models.DecimalField(max_digits=5, decimal_places=2,
                                  null=True, blank=True, db_column='Sperm_Vitality', help_text='%')
    normal_spermatozoa      = models.DecimalField(max_digits=5, decimal_places=2,
                                  null=True, blank=True, db_column='Normal_Spermatozoa', help_text='%')
    cytoplasmic_droplet     = models.DecimalField(max_digits=5, decimal_places=2,
                                  null=True, blank=True, db_column='Cytoplasmic_Droplet', help_text='%')
    teratozoospermia_index  = models.DecimalField(max_digits=5, decimal_places=2,
                                  null=True, blank=True, db_column='Teratozoospermia_Index')
    progressive_motility    = models.DecimalField(max_digits=5, decimal_places=2,
                                  null=True, blank=True, db_column='Progressive_Motility', help_text='%')
    high_dna_stainability   = models.DecimalField(max_digits=5, decimal_places=2,
                                  null=True, blank=True, db_column='High_DNA_Stainability', help_text='%')
    dna_fragmentation_index = models.DecimalField(max_digits=5, decimal_places=2,
                                  null=True, blank=True, db_column='DNA_Fragmentation_Index', help_text='%')

    class Meta:
        db_table = 'SpermSpecimen'
        verbose_name = 'Sperm Specimen'
        verbose_name_plural = 'Sperm Specimens'

    def __str__(self):
        return f"Sperm [{self.barcode}] — {self.patient}"


class OocyteSpecimen(models.Model):
    barcode              = models.CharField(max_length=50, primary_key=True)
    patient              = models.ForeignKey(PatientInformation, on_delete=models.CASCADE,
                               db_column='Patient_ID', related_name='oocyte_specimens')
    storage              = models.ForeignKey(SampleInventory, on_delete=models.SET_NULL,
                               null=True, blank=True, db_column='Storage_ID',
                               related_name='oocyte_specimens')
    collection_date      = models.DateField(null=True, blank=True, db_column='Collection_Date')
    maturity             = models.CharField(max_length=50, null=True, blank=True, db_column='Maturity')
    retrieval_method     = models.CharField(max_length=100, null=True, blank=True, db_column='Retrieval_Method')
    count                = models.IntegerField(null=True, blank=True, db_column='Count')
    fertilization_status = models.CharField(max_length=50, null=True, blank=True, db_column='Fertilization_Status')

    class Meta:
        db_table = 'OocyteSpecimen'
        verbose_name = 'Oocyte Specimen'
        verbose_name_plural = 'Oocyte Specimens'

    def __str__(self):
        return f"Oocyte [{self.barcode}] — {self.patient}"


class EmbryoInformation(models.Model):
    barcode         = models.CharField(max_length=50, primary_key=True)
    patient         = models.ForeignKey(PatientInformation, on_delete=models.CASCADE,
                          db_column='Patient_ID', related_name='embryos')
    storage         = models.ForeignKey(SampleInventory, on_delete=models.SET_NULL,
                          null=True, blank=True, db_column='Storage_ID',
                          related_name='embryos')
    collection_date = models.DateField(null=True, blank=True, db_column='Collection_Date')
    volume          = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_column='Volume')
    motility        = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                          db_column='Motility', help_text='%')
    concentration   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                          db_column='Concentration', help_text='million/mL')
    # M:M to SpermSpecimen and OocyteSpecimen via explicit junction tables
    sperm_sources   = models.ManyToManyField(SpermSpecimen, through='SpermEmbryo',
                          related_name='embryos', blank=True)
    oocyte_sources  = models.ManyToManyField(OocyteSpecimen, through='OocyteEmbryo',
                          related_name='embryos', blank=True)

    class Meta:
        db_table = 'EmbryoInformation'
        verbose_name = 'Embryo'
        verbose_name_plural = 'Embryos'

    def __str__(self):
        return f"Embryo [{self.barcode}] — {self.patient}"


class SpermEmbryo(models.Model):
    id     = models.AutoField(primary_key=True)
    sperm  = models.ForeignKey(SpermSpecimen,   on_delete=models.CASCADE,
                 db_column='Sperm_Barcode',  to_field='barcode')
    embryo = models.ForeignKey(EmbryoInformation, on_delete=models.CASCADE,
                 db_column='Embryo_Barcode', to_field='barcode')

    class Meta:
        db_table = 'Sperm_Embryo'
        unique_together = ('sperm', 'embryo')
        verbose_name = 'Sperm → Embryo Link'


class OocyteEmbryo(models.Model):
    id     = models.AutoField(primary_key=True)
    oocyte = models.ForeignKey(OocyteSpecimen,    on_delete=models.CASCADE,
                 db_column='Oocyte_Barcode', to_field='barcode')
    embryo = models.ForeignKey(EmbryoInformation, on_delete=models.CASCADE,
                 db_column='Embryo_Barcode', to_field='barcode')

    class Meta:
        db_table = 'Oocyte_Embryo'
        unique_together = ('oocyte', 'embryo')
        verbose_name = 'Oocyte → Embryo Link'
