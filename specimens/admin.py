from django.contrib import admin
from .models import SampleInventory, SpermSpecimen, OocyteSpecimen, EmbryoInformation


@admin.register(SampleInventory)
class SampleInventoryAdmin(admin.ModelAdmin):
    list_display = ('storage_id', 'storage_temperature')


class SpermEmbryoInline(admin.TabularInline):
    from .models import SpermEmbryo
    model = SpermEmbryo
    extra = 0
    verbose_name = 'Linked Sperm Specimen'


class OocyteEmbryoInline(admin.TabularInline):
    from .models import OocyteEmbryo
    model = OocyteEmbryo
    extra = 0
    verbose_name = 'Linked Oocyte Specimen'


@admin.register(SpermSpecimen)
class SpermSpecimenAdmin(admin.ModelAdmin):
    list_display  = ('barcode', 'patient', 'collection_date', 'sperm_concentration',
                     'total_sperm_count', 'progressive_motility', 'dna_fragmentation_index')
    list_filter   = ('collection_date',)
    search_fields = ('barcode', 'patient__last_name', 'patient__first_name')
    ordering      = ('-collection_date',)

    fieldsets = (
        ('Identification', {
            'fields': ('barcode', 'patient', 'storage', 'collection_date')
        }),
        ('Count & Volume', {
            'fields': ('sperm_concentration', 'total_sperm_count', 'ejaculate_volume')
        }),
        ('Morphology', {
            'fields': ('normal_spermatozoa', 'cytoplasmic_droplet', 'teratozoospermia_index')
        }),
        ('Motility & DNA', {
            'fields': ('sperm_vitality', 'progressive_motility',
                       'high_dna_stainability', 'dna_fragmentation_index')
        }),
    )


@admin.register(OocyteSpecimen)
class OocyteSpecimenAdmin(admin.ModelAdmin):
    list_display  = ('barcode', 'patient', 'collection_date', 'maturity',
                     'retrieval_method', 'count', 'fertilization_status')
    list_filter   = ('maturity', 'fertilization_status')
    search_fields = ('barcode', 'patient__last_name', 'patient__first_name')
    ordering      = ('-collection_date',)


@admin.register(EmbryoInformation)
class EmbryoInformationAdmin(admin.ModelAdmin):
    list_display  = ('barcode', 'patient', 'collection_date', 'volume', 'motility', 'concentration')
    search_fields = ('barcode', 'patient__last_name', 'patient__first_name')
    ordering      = ('-collection_date',)
    inlines       = [SpermEmbryoInline, OocyteEmbryoInline]
