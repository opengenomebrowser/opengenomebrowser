from django.core.paginator import Paginator
from django.shortcuts import render

from website.models import Annotation, PathwayMap
from website.models.Annotation import annotation_types

from website.views.helpers.magic_string import MagicQueryManager
from website.views.helpers.extract_requests import extract_data, get_or_none


# class FilteredListView(ListView):
#     filterset_class = None
#     pagination_options = [10, 20, 30, 50, 100, 500, 1000]
#     paginate_by = 30
#
#     def get_queryset(self):
#         # Get the queryset however you usually would.  For example:
#         queryset = super().get_queryset()
#         # Then use the query parameters and the queryset to
#         # instantiate a filterset and save it as an attribute
#         # on the view instance for later.
#         self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
#         # Return the filtered queryset
#         return self.filterset.qs.distinct()
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['filterset'] = self.filterset
#         context['paginated_by'] = self.paginate_by
#         if self.paginate_by not in self.pagination_options:
#             self.pagination_options.append(self.paginate_by)
#         context['pagination_options'] = self.pagination_options
#         return context
#
#     def get(self, request, *args, **kwargs):
#         paginate_by = request.GET.get('paginate_by', '')
#         if paginate_by == 'All':
#             self.paginate_by = None
#         elif paginate_by.isnumeric():
#             self.paginate_by = int(paginate_by)
#
#         return super().get(request, *args, **kwargs)
#
#
# class AnnotationFilterSet(FilterSet):
#     class Meta:
#         model = Annotation
#         fields = []
#
#     name_starts_with = django_filters.CharFilter(field_name='name', lookup_expr='istartswith')
#     name_contains = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
#     description_starts_with = django_filters.CharFilter(field_name='description', lookup_expr='istartswith')
#     description_contains = django_filters.CharFilter(field_name='description', lookup_expr='icontains')
#     genomes = django_filters.CharFilter(label='Genomes', method='filter_genomes')
#     anno_type = django_filters.ChoiceFilter(field_name='anno_type', choices=[(abbr, f'{at.name} ({abbr})') for abbr, at in annotation_types.items()])
#     pathwaymap = django_filters.filters.ModelChoiceFilter(label='Pathway map', queryset=PathwayMap.objects.all())
#
#     def filter_genomes(self, queryset, name, value):
#         qs = [v.strip() for v in value.split(',')]
#         magic_query_manager = MagicQueryManager(queries=qs)
#
#         for g in magic_query_manager.all_genomes:
#             queryset = queryset.filter(genomecontent__in=[g.identifier])
#         return queryset
#
#
# class AnnotationListView(FilteredListView):
#     template_name = 'website/annotation_filter.html'
#     model = Annotation
#     filterset_class = AnnotationFilterSet
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         if self.request.GET.get('genomes', False):
#             qs = [v.strip() for v in self.request.GET['genomes'].split(',')]
#
#             try:
#                 magic_query_manager = MagicQueryManager(queries=qs)
#                 context['magic_query_manager'] = magic_query_manager
#                 if len(magic_query_manager.all_genomes) == 0:
#                     context['error_danger'].append('Query did not find any genomes.')
#             except Exception as e:
#                 context['error_danger'] = context.get('error_danger', [])
#                 context['error_danger'].append(str(e))
#
#         return context
#
#
def simple_filter(qs, lookup_expr, field_id, request, context):
    query = get_or_none(request=request, key=field_id)
    if query:
        return qs.filter(**{lookup_expr: query}), context
    else:
        return qs, context


def genomes_filter(qs, lookup_expr, field_id, request, context):
    genomes = get_or_none(request=request, key=field_id, list=True, sep=',')
    if genomes:
        try:
            magic_query_manager = MagicQueryManager(queries=genomes)
            context['magic_query_manager'] = magic_query_manager
            if len(magic_query_manager.all_genomes) == 0:
                context['error_danger'].append('Query did not find any genomes.')
            for g in magic_query_manager.all_genomes:
                qs = qs.filter(genomecontent__in=[g.identifier])
        except Exception as e:
            context['error_danger'].append(str(e))

    return qs, context


class AnnotationFilter:
    filter_fields = dict(
        genomes=dict(
            label='Genomes', lookup_expr=None, filter_function=genomes_filter, hidden=True),
        name=dict(
            label='Name (regex)', lookup_expr='name__regex', filter_function=simple_filter),
        description=dict(
            label='Description (regex)', lookup_expr='description__regex', filter_function=simple_filter),
        anno_type=dict(
            label='Anno type', lookup_expr='anno_type', filter_function=simple_filter,
            choices=[('', '-------')] + [(abbr, f'{at.name} ({abbr})') for abbr, at in annotation_types.items()]),
        pathway_map=dict(
            label='Pathway map', lookup_expr='pathwaymap', filter_function=simple_filter,
            choices=[('', '-------')] + [(m.slug, str(m)) for m in PathwayMap.objects.all()])
    )

    paginate_by = 30
    pagination_options = ['All', 10, 20, 30, 50, 100, 500, 1000]

    @classmethod
    def filter_queryset(cls, request, context):
        qs = Annotation.objects
        filter_fields = cls.filter_fields.copy()
        for field_id, filter_field in filter_fields.items():
            filter_field['data'] = ''
            data = get_or_none(request=request, key=field_id)
            if data:
                filter_field['data'] = data
                filter_function = filter_field['filter_function']
                qs, context = filter_function(qs, filter_field['lookup_expr'], field_id, request, context)

        return qs.all(), filter_fields

    @classmethod
    def filter_view(cls, request):
        context = dict(
            title='Annotation filter',
            error_danger=[], error_warning=[], error_info=[]
        )

        filterset, filter_fields = cls.filter_queryset(request, context)

        context['filter_fields'] = filter_fields

        paginate_by = extract_data(request, 'paginate_by')
        if paginate_by == 'All':
            context['object_list'] = filterset
        else:
            paginate_by = int(paginate_by) if type(paginate_by) is str and paginate_by.isnumeric() else cls.paginate_by
            paginator = Paginator(filterset, paginate_by)
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
