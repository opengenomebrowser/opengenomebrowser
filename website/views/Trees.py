from django.shortcuts import render


def trees(request):
    context = dict(title='Trees')

    if 'genomes' in request.GET:
        genome_ids = request.GET['genomes'].split(' ')
    else:
        genome_ids = []

    context['key_genomes'] = genome_ids

    return render(request, 'website/trees.html', context)
