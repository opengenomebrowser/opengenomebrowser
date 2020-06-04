from django.shortcuts import render
from website.models import TaxID, Annotation, Member, Strain


def click_view(request):
    context = dict(
        title='Test Click Menu',
        taxids=TaxID.objects.all()[:5],
        annotations=Annotation.objects.all()[:5],
        members=Member.objects.all()[:5],
        strains=Strain.objects.all()[:5]
    )

    return render(request, 'global/test_click_menu.html', context)
