from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import SpermSpecimen, OocyteSpecimen, EmbryoInformation


def is_staff(user):
    return user.is_staff


@login_required(login_url='login')
@user_passes_test(is_staff, login_url='login')
def specimen_list(request):
    return render(request, 'specimen_list.html', {
        'sperm':   SpermSpecimen.objects.select_related('patient').order_by('-collection_date'),
        'oocytes': OocyteSpecimen.objects.select_related('patient').order_by('-collection_date'),
        'embryos': EmbryoInformation.objects.select_related('patient').order_by('-collection_date'),
    })
