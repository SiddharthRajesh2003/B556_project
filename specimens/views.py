from django.shortcuts import render
from .models import SpermSpecimen, OocyteSpecimen, EmbryoInformation


def specimen_list(request):
    return render(request, 'specimen_list.html', {
        'sperm':   SpermSpecimen.objects.select_related('patient').order_by('-collection_date'),
        'oocytes': OocyteSpecimen.objects.select_related('patient').order_by('-collection_date'),
        'embryos': EmbryoInformation.objects.select_related('patient').order_by('-collection_date'),
    })
