from django.shortcuts import render

from website.models.KeggMap import KeggMap


def kegg_view(request):
    context = {}

    if 'map' in request.GET:
        key_map = request.GET['map']
        context['key_map'] = key_map
        context['map_name'] = KeggMap.objects.get(map_id=key_map).map_name

    if 'genomes' in request.GET:
        context['key_genomes'] = request.GET['genomes'].split(' ')

    print(context)

    return render(request, 'website/kegg.html', context)
