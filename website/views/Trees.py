from django.shortcuts import render, HttpResponse


def trees(request):
    context = dict(title='Trees')

    if 'members' in request.GET:
        member_ids = request.GET['members'].split(' ')
    else:
        member_ids = []

    context['key_members'] = member_ids

    return render(request, 'website/trees.html', context)
