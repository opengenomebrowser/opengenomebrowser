from django.core.exceptions import FieldError
from django.core.paginator import Paginator
from django.shortcuts import render

from website.models import Annotation, PathwayMap
from website.models.Annotation import annotation_types
from website.views.helpers.extract_errors import extract_errors

from website.views.helpers.magic_string import MagicQueryManager
from website.views.helpers.extract_requests import extract_data, extract_data_or


def simple_filter(qs, lookup_expr, field_id, request, context):
    query = extract_data_or(request=request, key=field_id)
    if query:
        return qs.filter(**{lookup_expr: query}), context
    else:
        return qs, context


def genomes_filter(qs, lookup_expr, field_id, request, context):
    mgm_id = 'magic_query_manager' if field_id == 'genomes' else 'magic_query_manager_not'
    genomes = extract_data_or(request=request, key=field_id, list=True, sep=',')

    if genomes:
        try:
            magic_query_manager = MagicQueryManager(queries=genomes)
            context[mgm_id] = magic_query_manager
            if len(magic_query_manager.all_genomes) == 0:
                context['error_danger'].append('Query did not find any genomes.')
            for g in magic_query_manager.all_genomes:
                if field_id == 'genomes':
                    qs = qs.filter(genomecontent__in=[g.identifier])
                else:
                    qs = qs.exclude(genomecontent__in=[g.identifier])
        except Exception as e:
            context['error_danger'].append(str(e))

    return qs, context


def get_pathways() -> list:
    try:
        return [(m.slug, str(m)) for m in PathwayMap.objects.all()]
    except:
        from logging import warning
        warning('Could not get PathwayMap objects.')
        return []


class AnnotationFilter:
    filter_fields = dict(
        genomes=dict(
            label='Genomes', lookup_expr=None, filter_function=genomes_filter, hidden=True),
        not_genomes=dict(
            label='Not genomes', lookup_expr=None, filter_function=genomes_filter, hidden=True),
        name=dict(
            label='Name (regex)', lookup_expr='name__regex', filter_function=simple_filter),
        description=dict(
            label='Description (regex)', lookup_expr='description__regex', filter_function=simple_filter),
        anno_type=dict(
            label='Anno type', lookup_expr='anno_type', filter_function=simple_filter,
            choices=[('', '-------')] + [(abbr, f'{at.name} ({abbr})') for abbr, at in annotation_types.items()]),
        pathway_map=dict(
            label='Pathway map', lookup_expr='pathwaymap', filter_function=simple_filter,
            choices=[('', '-------')] + get_pathways())
    )

    paginate_by = 30
    pagination_options = ['All', 10, 20, 30, 50, 100, 500, 1000]

    @classmethod
    def filter_queryset(cls, request, context):
        qs = Annotation.objects
        filter_fields = cls.filter_fields.copy()
        for field_id, filter_field in filter_fields.items():
            filter_field['data'] = ''
            data = extract_data_or(request=request, key=field_id)
            if data:
                filter_field['data'] = data
                filter_function = filter_field['filter_function']
                qs, context = filter_function(qs, filter_field['lookup_expr'], field_id, request, context)

        return qs.all(), filter_fields

    @classmethod
    def filter_view(cls, request):
        context = extract_errors(request, dict(title='Annotation filter'))

        qs, filter_fields = cls.filter_queryset(request, context)

        # order queryset consistent results with pagination
        order_by = extract_data_or(request, 'order_by', default='name')
        try:
            qs = qs.order_by(order_by)
        except FieldError:
            context['error_danger'].append(f"Could not order_by '{order_by}', ordering by 'name' instead.")
            qs = qs.order_by('name')

        context['filter_fields'] = filter_fields

        paginate_by = extract_data(request, 'paginate_by')
        if paginate_by == 'All':
            context['object_list'] = qs
        else:
            paginate_by = int(paginate_by) if type(paginate_by) is str and paginate_by.isnumeric() else cls.paginate_by
            paginator = Paginator(qs, paginate_by)
            try:
                page = int(extract_data(request, 'page'))
            except:
                page = 1

            page_obj = paginator.page(page)
            context['page_obj'] = page_obj
            context['object_list'] = page_obj.object_list
            context['paginator'] = paginator

        context['paginated_by'] = paginate_by
        context['pagination_options'] = cls.pagination_options
        if paginate_by not in cls.pagination_options:
            context['pagination_options'].append(paginate_by)

        return render(request, 'website/annotation_filter.html', context)
