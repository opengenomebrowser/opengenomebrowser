from django.core.paginator import Paginator
from django.shortcuts import render
from django.db.models import Case, When, F, Value, CharField, BooleanField, ExpressionWrapper, Q
from django.db.models.manager import Manager
from django.db.models.functions import Concat
from django.contrib.postgres.aggregates import StringAgg

from OpenGenomeBrowser import settings
from website.models import Genome, TaxID, Tag
from website.views.helpers.extract_requests import extract_data, extract_data_or


class RenderFunctions:
    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def get_representative_html(qs: Manager):
        return qs.annotate(
            # 'True' or 'False'
            representative__isnull_html=
            ExpressionWrapper(
                Q(representative__isnull=False),
                output_field=BooleanField()
            )
        )

    @staticmethod
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

    @staticmethod
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


class Choices:
    @staticmethod
    def genome_tags():
        return [(t.tag, t.tag) for t in Tag.objects.filter(genome__isnull=False).distinct()]

    @staticmethod
    def organism_tags():
        return [(t.tag, t.tag) for t in Tag.objects.filter(organism__isnull=False).distinct()]


from website.views.helpers.Columns import \
    Column, SimpleColumn, BinaryColumn, TagColumn, DateRangeColumn, RangeColumn, PercentageRangeColumn, TaxColumn, ListColumn


class GenomeFilter:
    column_classes = [SimpleColumn, BinaryColumn, TagColumn, DateRangeColumn, RangeColumn, PercentageRangeColumn, TaxColumn, ListColumn]

    @staticmethod
    def __get_columns() -> dict[str, Column]:
        Columns = [
            SimpleColumn('Organism', lookup_expr='organism__name', annotate_queryset_fn=RenderFunctions.get_organism_html),
            SimpleColumn('Identifier', annotate_queryset_fn=RenderFunctions.get_genome_html),
            SimpleColumn('Old Identifier'),

            BinaryColumn('Representative', lookup_expr='representative__isnull', choices=[('', 'Both'), ('True', 'True'), ('False', 'False')],
                         annotate_queryset_fn=RenderFunctions.get_representative_html),
            BinaryColumn('Restricted', lookup_expr='organism__restricted', choices=[('', 'Both'), ('True', 'True'), ('False', 'False')]),
            BinaryColumn('Contaminated', choices=[('', 'Both'), ('True', 'True'), ('False', 'False')]),

            TagColumn('Genome Tags', lookup_expr='tags', choices=Choices.genome_tags, annotate_queryset_fn=RenderFunctions.get_genome_tags_html),
            TagColumn('Organism Tags', lookup_expr='organism__tags', choices=Choices.organism_tags,
                      annotate_queryset_fn=RenderFunctions.get_organism_tags_html),

            SimpleColumn('Growth Condition'),
            SimpleColumn('Geographical Coordinates'),
            SimpleColumn('Geographical Name'),
            SimpleColumn('Library Preparation'),
            SimpleColumn('Sequencing Technology', lookup_expr='sequencing_tech'),
            SimpleColumn('Sequencing Technology Version', lookup_expr='sequencing_tech_version'),
            SimpleColumn('Read Length'),
            SimpleColumn('Sequencing Coverage'),
            SimpleColumn('Assembly Tool'),
            SimpleColumn('Assembly Tool Version', lookup_expr='assembly_version'),
            SimpleColumn('CDS Tool'),
            SimpleColumn('CDS Tool Version'),
            SimpleColumn('Bioproject', lookup_expr='bioproject_accession'),
            SimpleColumn('Biosample', lookup_expr='biosample_accession'),
            SimpleColumn('Genome Accession'),

            DateRangeColumn('Isolation date'),
            DateRangeColumn('Sequencing Date'),
            DateRangeColumn('Assembly Date'),
            DateRangeColumn('CDS Tool Date'),

            RangeColumn('Assembly Longest Scf'),
            RangeColumn('Assembly Size'),
            RangeColumn('Assembly # Scaffolds'),
            RangeColumn('Assembly N50'),
            RangeColumn('Assembly # Gaps', lookup_expr='assembly_gaps'),
            RangeColumn('Assembly # N', lookup_expr='assembly_ncount'),
            RangeColumn('Assembly # Replicons', lookup_expr='nr_replicons'),
            RangeColumn('Number of Genes', lookup_expr='genomecontent__n_genes'),

            PercentageRangeColumn('GC content [%]', id='assembly_gc', lookup_expr='assembly_gc'),
            PercentageRangeColumn('BUSCO [%S]', id='busco_s', lookup_expr='BUSCO_percent_single'),

            TaxColumn('Tax:Superkingdom', lookup_expr='organism__taxid__taxsuperkingdom'),
            TaxColumn('Tax:Phylum', lookup_expr='organism__taxid__taxphylum'),
            TaxColumn('Tax:Class', lookup_expr='organism__taxid__taxclass'),
            TaxColumn('Tax:Order', lookup_expr='organism__taxid__taxorder'),
            TaxColumn('Tax:Family', lookup_expr='organism__taxid__taxfamily'),
            TaxColumn('Tax:Genus', lookup_expr='organism__taxid__taxgenus'),
            TaxColumn('Tax:Species', lookup_expr='organism__taxid__taxspecies'),
            TaxColumn('Tax:Subspecies', lookup_expr='organism__taxid__taxsubspecies'),
            TaxColumn('Taxonomy', lookup_expr='organism__taxid__taxscientificname'),
            TaxColumn('TaxID', lookup_expr='organism__taxid__id'),

            ListColumn('Broad Isolation Environment', id='env_broad', lookup_expr='env_broad_scale'),
            ListColumn('Local Isolation Environment', id='env_local', lookup_expr='env_local_scale'),
            ListColumn('Environment Medium', lookup_expr='env_medium'),
            ListColumn('Literature References'),
        ]
        return {f.id: f for f in Columns}

    paginate_by = 30
    pagination_options = ['All', 10, 20, 30, 50, 100, 500, 1000]

    @classmethod
    def filter_queryset(cls, request, context, active_filters) -> Manager:
        qs = Genome.objects.prefetch_related('genomecontent', 'organism', 'organism__taxid')

        for filter in active_filters:
            try:
                qs = filter.filter(qs, request)
            except Exception as e:
                context['error_danger'].append(str(filter) + str(e))

        return qs

    @classmethod
    def filter_view(cls, request):
        context = dict(
            title='Genome table',
            error_danger=[], error_warning=[], error_info=[]
        )

        context['activate_js'] = [c.activate_js() for c in cls.column_classes]
        context['submit_js'] = [c.submit_js() for c in cls.column_classes]

        all_columns = cls.__get_columns()

        active_columns = extract_data_or(request=request, key='columns', list=True, sep=',', default=settings.DEFAULT_GENOMES_COLUMNS_new)
        active_filters = set(all_columns.keys()).intersection(set(request.GET.keys()).union(set(request.POST.keys())))
        shown_filters = active_columns + [f for f in active_filters if f not in active_columns]

        try:
            active_columns = {c: all_columns[c] for c in active_columns}
        except KeyError:
            context['error_danger'].append(f'Failed to load columns: {[c for c in active_columns if c not in all_columns]}')
            return render(request, 'website/genome_filter.html', context)

        shown_filters = {f: all_columns[f] for f in shown_filters}
        active_filters = {f.id: f for f in all_columns.values() if f.id in active_filters}

        context['all_columns'] = all_columns
        context['active_columns'] = active_columns
        context['shown_filters'] = shown_filters

        qs = cls.filter_queryset(request, context, active_filters.values())
        qs = cls.annotate_qs(qs=qs, columns=[f for f in all_columns.values() if f.id in active_columns or f.id in active_filters.values()])
        qs = cls.order_qs(qs=qs, request=request, columns=all_columns)

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

        column_lookups = [f.lookup_expr
                          if f.annotate_queryset is None
                          else f.lookup_expr + '_html'
                          for f in active_columns.values()]

        for col in ['restricted', 'contaminated', 'representative']:
            if col not in active_columns and col in column_lookups:
                column_lookups.remove(col)

        context['table'] = context['object_list'].values_list(*column_lookups)

        context['paginated_by'] = paginate_by
        context['pagination_options'] = cls.pagination_options
        if paginate_by not in cls.pagination_options:
            context['pagination_options'].append(paginate_by)

        return render(request, 'website/genome_filter.html', context)

    @staticmethod
    def annotate_qs(qs, columns: [Column]):
        for column in columns:
            if column.annotate_queryset is not None:
                qs = column.annotate_queryset(qs)
        return qs

    @staticmethod
    def order_qs(qs, request, columns: [Column]):
        sort_column = extract_data_or(request=request, key='sort', default='identifier')
        asc = extract_data_or(request=request, key='asc', default='True')
        asc = (asc.lower() == 'true')
        return columns[sort_column].sort(qs=qs, asc=asc)
