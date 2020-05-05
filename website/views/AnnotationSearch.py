from django.shortcuts import render, HttpResponse

from website.models import Genome
from website.models.Annotation import Annotation


def annotation_view(request):
    context = {}

    if 'members' in request.GET:
        context['key_members'] = request.GET['members'].split(' ')

    if 'annotations' in request.GET:
        context['key_annotations'] = request.GET['annotations'].split(' ')

    return render(request, 'website/annotation_search.html', context)


def annotation_matrix(request):
    context = {}

    # check input
    if not 'members[]' and 'annotations[]' in request.POST:
        return HttpResponse('Request failed! Please POST members[] and annotations[].')

    members = set(request.POST.getlist('members[]'))
    try:
        members = [Genome.objects.get(identifier=identifier) for identifier in members]
    except Annotation.DoesNotExist:
        return HttpResponse('Request failed: members[] incorrect.')

    annotations = set(request.POST.getlist('annotations[]'))
    try:
        annotations = [Annotation.objects.get(name=anno) for anno in annotations]
    except Annotation.DoesNotExist:
        return HttpResponse('Request failed: annotations[] incorrect.')

    # create patterns
    pattern_to_members = create_patterns(members, annotations)
    # sort patterns
    pattern_to_members, groups = sort_pattern_dict(pattern_to_members)

    table_header, table_body, table_foot = create_coverage_matrix(pattern_to_members, annotations)

    # print(pattern_to_members)
    # print('num_patterns:', len(pattern_to_members))
    # print(table_header)
    # for row in table_body:
    #     print(row)
    # print(table_foot)
    # print(groups)

    context = dict(
        table_header=table_header,
        table_body=table_body,
        table_foot=table_foot,
        groups=groups
    )

    return render(request, 'website/annotation_matrix.html', context)

def create_coverage_matrix(pattern_to_members:dict, annotations:list):
    table_header = [""]
    table_header.extend(['g' + str(i) for i in range(1, len(pattern_to_members) + 1)])

    table_body = []  # each row stands for a row in the table
    for i, annotation in enumerate(annotations):
        table_row = [annotation]
        table_row.extend([pattern[i] for pattern in pattern_to_members])
        table_body.append(table_row)

    table_body = sort_table_body(table_body)

    table_foot = [len(members) for members in pattern_to_members.values()]

    return table_header, table_body, table_foot


def create_patterns(members:list, annotations:list) -> dict:
    pattern_to_members = {}
    for member in members:
        pattern = get_pattern(member, annotations)
        if pattern in pattern_to_members:
            pattern_to_members[pattern].append(member)
        else:
            pattern_to_members[pattern] = [member]
    return pattern_to_members

def get_pattern(member: Genome, annotations: list) -> tuple:
    """
    :returns a tuple of len(annotations) filled with booleans: True if member covers annotation
    Example: (False, False, False, True, False)
    """
    pattern = list()
    for annotation in annotations:
        try:
            annotation.genome_set.get(identifier=member.identifier)
            pattern.append(True)
        except Genome.DoesNotExist:
            pattern.append(False)
    return tuple(pattern)  # tuples are hashable


def sort_pattern_dict(pattern_to_sth: dict) -> dict:
    # sort pattern_to_members by most covered pattern
    def sorting_function(pattern: tuple) -> int:
        return sum(pattern)

    patterns_sorted = sorted(pattern_to_sth, key=sorting_function, reverse=True)
    final_pattern = {pattern: pattern_to_sth[pattern] for pattern in patterns_sorted}

    groups = list(final_pattern.values())
    return final_pattern, groups

def sort_table_body(table_body: list) -> list:
    # sort table_body by most common annotation
    def sorting_function(bools: list) -> int:
        return sum(bools[1:])  # remove first element, which is an annotation-object

    return sorted(table_body, key=sorting_function, reverse=True)
