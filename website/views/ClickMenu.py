from django.shortcuts import render
from website.models import TaxID, Annotation, Genome, Organism, Gene


def click_view(request):
    context = dict(
        title='Test Click Menu',
        taxids=TaxID.objects.all()[:5],
        annotations=Annotation.objects.all()[:5],
        genomes=Genome.objects.all()[:5],
        organisms=Organism.objects.all()[:5],
        genes=Gene.objects.all()[:5]
    )

    return render(request, 'global/test_click_menu.html', context)
