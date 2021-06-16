from django.core.paginator import Paginator
from django.shortcuts import render

from OpenGenomeBrowser import settings
from website.models import Genome, TaxID
from website.models.Annotation import annotation_types
from website.views.helpers.extract_requests import extract_data, extract_data_or
from website.views.helpers.magic_string import MagicQueryManager

from django.db.models.manager import Manager
from django.db.models.functions import Concat

from django.contrib.postgres.aggregates import StringAgg

from django.db.models import Case, Value, When, Count, Exists, F, Value, CharField


def simple_filter(qs, column, filter_field, request, context):
    query = extract_data_or(request=request, key=column)
    lookup_expr = filter_field['lookup_expr']
    if query:
        return query, qs.filter(**{lookup_expr + '__regex': query}), context
    else:
        return query, qs, context


def tags_filter(qs, column, filter_field, request, context):
    raise NotImplementedError
    return query, qs, context


def list_filter(qs, column, filter_field, request, context):
    raise NotImplementedError
    return query, qs, context


def binary_filter(qs, column, filter_field, request, context):
    query = extract_data_or(request=request, key=column)
    lookup_expr = filter_field['lookup_expr']
    if query:
        assert query in ['True', 'False']
        query = query == 'True'
        if lookup_expr.endswith('__isnull'):
            query = not query
        return qs.filter(**{lookup_expr: query}), context
    else:
        return query, qs, context


def date_filter(qs, column, filter_field, request, context):
    raise NotImplementedError
    return query, qs, context


def int_range_filter(qs, column, filter_field, request, context):
    raise NotImplementedError
    return query, qs, context


def percentage_range_filter(qs, column, filter_field, request, context):
    raise NotImplementedError
    return query, qs, context


def tax_filter(qs, column, filter_field, request, context):
    tax = extract_data(request=request, key=column, list=True, sep=',')
    if column == 'taxid':
        column = 'id'
        tax = [int(t) for t in tax]
    qs = qs.filter(**{f'organism__taxid__{column}__in': tax})
    return tax, qs, context


def get_genome_html(qs: Manager):
    return qs.annotate(
        # F'<span class="genome ogb-tag" data-species="{taxscientificname}">{identifier}</span>'
        identifier_html=Concat(
            Value('<span class="genome ogb-tag'),
            Case(
                When(
                    representative__isnull=True,
                    then=Value(' no-representative')
                )
            ),
            Case(
                When(
                    contaminated=True,
                    then=Value(' contaminated')
                )
            ),
            Case(
                When(
                    organism__restricted=True,
                    then=Value(' restricted')
                )
            ),
            Value('" data-species="'),
            F('organism__taxid__taxscientificname'),
            Value('">'),
            F('identifier'),
            Value('</span>'),
            output_field=CharField()
        )
    )


def get_organism_html(qs: Manager):
    return qs.annotate(
        # F'<span class="organism ogb-tag" data-species="{taxscientificname}">{name}</span>'
        organism__name_html=Concat(
            Value('<span class="organism ogb-tag'),
            Case(
                When(
                    organism__restricted=True,
                    then=Value(' restricted')
                )
            ),
            Value('" data-species="'),
            F('organism__taxid__taxscientificname'),
            Value('">'),
            F('organism__name'),
            Value('</span>'),
            output_field=CharField()
        )
    )


from django.db.models import BooleanField, ExpressionWrapper, Q


def get_representative_html(qs: Manager):
    return qs.annotate(
        # 'True' or 'False'
        representative__isnull_html=
        ExpressionWrapper(
            Q(representative__isnull=False),
            output_field=BooleanField()
        )
    )


def get_genome_tags_html(qs: Manager):
    return qs.annotate(
        # f'<span class="tag ogb-tag" data-tag="{tag}" title="{description}">{tag}</span>'
        tags_html=StringAgg(
            Case(
                When(
                    tags__isnull=False,
                    then=Concat(
                        Value('<span class="tag ogb-tag" data-tag="'),
                        F('tags__tag'), Value('" title="'),
                        F('tags__description'),
                        Value('">'),
                        F('tags__tag'),
                        Value('</span>'),
                        output_field=CharField()
                    )
                )
            ),
            delimiter=''
        )
    )


def get_organism_tags_html(qs: Manager):
    return qs.annotate(
        # f'<span class="tag ogb-tag" data-tag="{tag}" title="{description}">{tag}</span>'
        organism__tags_html=StringAgg(
            Case(
                When(
                    organism__tags__isnull=False,
                    then=Concat(
                        Value('<span class="tag ogb-tag" data-tag="'),
                        F('organism__tags__tag'), Value('" title="'),
                        F('organism__tags__description'),
                        Value('">'),
                        F('organism__tags__tag'),
                        Value('</span>'),
                        output_field=CharField()
                    )
                )
            ),
            delimiter=''
        )
    )


choice_superkingdom = [(t.taxscientificname, t.taxscientificname) for t in TaxID.objects.filter(rank='superkingdom').all()]
choice_phylum = [(t.taxscientificname, t.taxscientificname) for t in TaxID.objects.filter(rank='phylum').all()]
choice_class = [(t.taxscientificname, t.taxscientificname) for t in TaxID.objects.filter(rank='class').all()]
choice_order = [(t.taxscientificname, t.taxscientificname) for t in TaxID.objects.filter(rank='order').all()]
choice_family = [(t.taxscientificname, t.taxscientificname) for t in TaxID.objects.filter(rank='family').all()]
choice_genus = [(t.taxscientificname, t.taxscientificname) for t in TaxID.objects.filter(rank='genus').all()]
choice_species = [(t.taxscientificname, t.taxscientificname) for t in TaxID.objects.filter(rank='species').all()]
choice_subspecies = [(t.taxscientificname, t.taxscientificname) for t in TaxID.objects.filter(rank='subspecies').all()]
choice_scientificname = [(t.taxscientificname, t.taxscientificname) for t in TaxID.objects.all()]
choice_taxid = [(t.id, f'{t.id} ({t.taxscientificname})') for t in TaxID.objects.all()]


class GenomeFilter:
    @staticmethod
    def __get_filter_fields():
        return {
            'organism': {'lookup_expr': 'organism__name', 'filter_function': simple_filter, 'label': 'Organism', 'render_fn': get_organism_html},
            'identifier': {'lookup_expr': 'identifier', 'filter_function': simple_filter, 'label': 'Identifier', 'render_fn': get_genome_html},
            'old_identifier': {'lookup_expr': 'old_identifier', 'filter_function': simple_filter, 'label': 'Old Identifier'},
            'representative': {'lookup_expr': 'representative__isnull', 'filter_function': binary_filter,
                               'choices': [('', 'Both'), ('True', 'True'), ('False', 'False')],
                               'label': 'Representative', 'render_fn': get_representative_html},
            'restricted': {'lookup_expr': 'organism__restricted', 'filter_function': binary_filter,
                           'choices': [('', 'Both'), ('True', 'True'), ('False', 'False')],
                           'label': 'Restricted'},
            'contaminated': {'lookup_expr': 'contaminated', 'filter_function': binary_filter,
                             'choices': [('', 'Both'), ('True', 'True'), ('False', 'False')],
                             'label': 'Contaminated'},
            'genome_tags': {'lookup_expr': 'tags', 'filter_function': tags_filter, 'label': 'Genome-Tags', 'render_fn': get_genome_tags_html},
            'organism_tags': {'lookup_expr': 'organism__tags', 'filter_function': tags_filter, 'label': 'Organism-Tags',
                              'render_fn': get_organism_tags_html},
            'isolation_date': {'lookup_expr': 'isolation_date', 'filter_function': date_filter, 'label': 'Isolation date'},
            'env_broad_scale': {'lookup_expr': 'env_broad_scale__contains', 'filter_function': list_filter, 'label': 'Broad Isolation Environment'},
            'env_local_scale': {'lookup_expr': 'env_local_scale__contains', 'filter_function': list_filter, 'label': 'Local Isolation Environment'},
            'env_medium': {'lookup_expr': 'env_medium__contains', 'filter_function': list_filter, 'label': 'Environment Medium'},
            'growth_condition': {'lookup_expr': 'growth_condition', 'filter_function': simple_filter, 'label': 'Growth Condition'},
            'geographical_coordinates': {'lookup_expr': 'geographical_coordinates', simple_filter: list_filter, 'label': 'Isolation Coordinates'},
            'geographical_name': {'lookup_expr': 'geographical_name', 'filter_function': simple_filter, 'label': 'Geographical Name'},
            'library_preparation': {'lookup_expr': 'library_preparation', 'filter_function': simple_filter, 'label': 'Library Preparation'},
            'sequencing_tech': {'lookup_expr': 'sequencing_tech', 'filter_function': simple_filter, 'label': 'Sequencing Technology'},
            'sequencing_tech_version': {'lookup_expr': 'sequencing_tech_version', 'filter_function': simple_filter,
                                        'label': 'Sequencing Technology Version'},
            'sequencing_date': {'lookup_expr': 'sequencing_date', 'filter_function': date_filter, 'label': 'Sequencing Date'},
            'read_length': {'lookup_expr': 'read_length', 'filter_function': int_range_filter, 'label': 'Read Length'},
            'sequencing_coverage': {'lookup_expr': 'sequencing_coverage', 'filter_function': simple_filter, 'label': 'Sequencing Coverage'},
            'assembly_tool': {'lookup_expr': 'assembly_tool', 'filter_function': simple_filter, 'label': 'Assembly Tool'},
            'assembly_version': {'lookup_expr': 'assembly_version', 'filter_function': simple_filter, 'label': 'Assembly Tool Version'},
            'assembly_date': {'lookup_expr': 'assembly_date', 'filter_function': date_filter, 'label': 'Assembly Date'},
            'assembly_gc': {'lookup_expr': 'assembly_gc', 'filter_function': percentage_range_filter, 'label': 'Assembly GC content [%]'},
            'assembly_longest_scf': {'lookup_expr': 'assembly_longest_scf', 'filter_function': int_range_filter, 'label': 'Assembly Longest Scf'},
            'assembly_size': {'lookup_expr': 'assembly_size', 'filter_function': int_range_filter, 'label': 'Assembly Size'},
            'assembly_nr_scaffolds': {'lookup_expr': 'assembly_nr_scaffolds', 'filter_function': int_range_filter, 'label': 'Assembly #Scfs'},
            'assembly_n50': {'lookup_expr': 'assembly_n50', 'filter_function': int_range_filter, 'label': 'Assembly N50'},
            'assembly_gaps': {'lookup_expr': 'assembly_gaps', 'filter_function': int_range_filter, 'label': 'Number of gaps'},
            'assembly_ncount': {'lookup_expr': 'assembly_ncount', 'filter_function': int_range_filter, 'label': 'Total Ns'},
            'nr_replicons': {'lookup_expr': 'nr_replicons', 'filter_function': int_range_filter, 'label': 'Assembly #Replicons'},
            'cds_tool': {'lookup_expr': 'cds_tool', 'filter_function': simple_filter, 'label': 'CDS Tool'},
            'cds_tool_version': {'lookup_expr': 'cds_tool_version', 'filter_function': simple_filter, 'label': 'CDS Tool Version'},
            'cds_tool_date': {'lookup_expr': 'cds_tool_date', 'filter_function': date_filter, 'label': 'CDS Date'},
            'genomecontent__n_genes': {'lookup_expr': 'genomecontent__n_genes', 'filter_function': int_range_filter, 'label': 'Number of genes'},
            'BUSCO_percent_single': {'lookup_expr': 'BUSCO_percent_single', 'filter_function': percentage_range_filter, 'label': 'BUSCO [%S]'},
            'bioproject_accession': {'lookup_expr': 'bioproject_accession', 'filter_function': simple_filter, 'label': 'Bioproject'},
            'biosample_accession': {'lookup_expr': 'biosample_accession', 'filter_function': simple_filter, 'label': 'Biosample'},
            'genome_accession': {'lookup_expr': 'genome_accession', 'filter_function': simple_filter, 'label': 'Genome Accession'},
            'literature_references': {'lookup_expr': 'literature_references', 'filter_function': list_filter, 'label': 'Literature References'},
            'taxsuperkingdom': {'lookup_expr': 'organism__taxid__taxsuperkingdom', 'filter_function': tax_filter, 'label': 'Tax:Superkingdom',
                                'choices': choice_superkingdom, 'multiple': True},
            'taxphylum': {'lookup_expr': 'organism__taxid__taxphylum', 'filter_function': tax_filter, 'label': 'Tax:Phylum',
                          'choices': choice_phylum, 'multiple': True},
            'taxclass': {'lookup_expr': 'organism__taxid__taxclass', 'filter_function': tax_filter, 'label': 'Tax:Class',
                         'choices': choice_class, 'multiple': True},
            'taxorder': {'lookup_expr': 'organism__taxid__taxorder', 'filter_function': tax_filter, 'label': 'Tax:Order',
                         'choices': choice_order, 'multiple': True},
            'taxfamily': {'lookup_expr': 'organism__taxid__taxfamily', 'filter_function': tax_filter, 'label': 'Tax:Family',
                          'choices': choice_family, 'multiple': True},
            'taxgenus': {'lookup_expr': 'organism__taxid__taxgenus', 'filter_function': tax_filter, 'label': 'Tax:Genus',
                         'choices': choice_genus, 'multiple': True},
            'taxspecies': {'lookup_expr': 'organism__taxid__taxspecies', 'filter_function': tax_filter, 'label': 'Tax:Species',
                           'choices': choice_species, 'multiple': True},
            'taxsubspecies': {'lookup_expr': 'organism__taxid__taxsubspecies', 'filter_function': tax_filter, 'label': 'Tax:Subspecies',
                              'choices': choice_subspecies, 'multiple': True},
            'taxscientificname': {'lookup_expr': 'organism__taxid__taxscientificname', 'filter_function': tax_filter,
                                  'label': 'Taxonomy',
                                  'choices': choice_scientificname, 'multiple': True},
            'taxid': {'lookup_expr': 'organism__taxid__id', 'filter_function': tax_filter, 'label': 'TaxID',
                      'choices': choice_taxid, 'multiple': True}
        }

    paginate_by = 30
    pagination_options = ['All', 10, 20, 30, 50, 100, 500, 1000]

    @classmethod
    def filter_queryset(cls, request, context, filter_fields):
        qs = Genome.objects.prefetch_related('genomecontent', 'organism', 'organism__taxid')
        columns = set(filter_fields.keys())
        current_filters = columns.intersection(set(request.GET.keys()).union(set(request.POST.keys())))

        current_filters = {c: f for c, f in filter_fields.items() if c in current_filters}

        for column, filter_field in current_filters.items():
            filter_function = filter_field['filter_function']
            data, qs, context = filter_function(qs, column, filter_field, request, context)
            filter_field['data'] = data

        return qs, current_filters

    @classmethod
    def filter_view(cls, request):
        context = dict(
            title='Genome table',
            error_danger=[], error_warning=[], error_info=[]
        )

        filter_fields = cls.__get_filter_fields()

        columns = extract_data_or(request=request, key='columns', list=True, sep=',', default=settings.DEFAULT_GENOMES_COLUMNS_new)

        qs, current_filters = cls.filter_queryset(request, context, filter_fields)

        qs = cls.annotate_qs(qs=qs, columns=columns, filter_fields=filter_fields)

        for column, filter_field in filter_fields.items():
            filter_field['hidden'] = not (column in current_filters or column in columns)

        context['columns'] = columns
        context['columns_data'] = {c: filter_fields[c] for c in columns}
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

        lookup_cols = [
            filter_fields[c]['lookup_expr']
            if 'render_fn' not in filter_fields[c]
            else filter_fields[c]['lookup_expr'] + '_html'
            for c in columns]
        context['table'] = context['object_list'].values_list(*lookup_cols)

        context['paginated_by'] = paginate_by
        context['pagination_options'] = cls.pagination_options
        if paginate_by not in cls.pagination_options:
            context['pagination_options'].append(paginate_by)

        return render(request, 'website/genome_filter.html', context)

    @staticmethod
    def annotate_qs(qs, columns, filter_fields):
        for column in columns:
            render_fn = filter_fields[column].get('render_fn', None)
            if render_fn:
                qs = render_fn(qs)
        return qs
