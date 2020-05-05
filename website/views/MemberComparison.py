from django.shortcuts import render, HttpResponse
from django.http import HttpResponseBadRequest

from website.models import Genome, Member, ANI, TaxID


def compare_members(request):
    context = {}

    if not 'members' in request.GET:
        return HttpResponseBadRequest('No members specified')

    member_ids = request.GET['members'].split(' ')

    print(member_ids)

    context['member_identifiers'] = member_ids

    # genomes = Genome.objects.filter(identifier__in=member_ids)
    # members = Member.objects.filter(identifier__in=member_ids)
    #
    # if not len(genomes) == len(members) == len(member_ids):
    #     return HttpResponseBadRequest('One or more member identifiers was wrong.')

    return render(request, 'website/member_comparison.html', context)
