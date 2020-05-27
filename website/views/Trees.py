from django.shortcuts import render, HttpResponse
from django.http import HttpResponseBadRequest

from website.models import Genome, Member, ANI, TaxID


def trees(request):
    context = {}

    if 'members' in request.GET:
        member_ids = request.GET['members'].split(' ')
    else:
        member_ids = []

    context['key_members'] = member_ids

    # genomes = Genome.objects.filter(identifier__in=member_ids)
    # members = Member.objects.filter(identifier__in=member_ids)
    #
    # if not len(genomes) == len(members) == len(member_ids):
    #     return HttpResponseBadRequest('One or more member identifiers was wrong.')

    return render(request, 'website/trees.html', context)
