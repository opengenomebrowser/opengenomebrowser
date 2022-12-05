from django.core.paginator import Paginator
from django.shortcuts import render
from django.db.models.manager import Manager

from OpenGenomeBrowser import settings
from website.models import Genome, TaxID, Tag
from website.models.helpers import AnnotatedGenomeManager
from website.views.helpers.extract_errors import extract_errors
from website.views.helpers.extract_requests import extract_data, extract_data_or

from website.views.helpers.Columns import \
    Column, SimpleColumn, BinaryColumn, MultipleRelatedColumn, DateRangeColumn, RangeColumn, PercentageRangeColumn, TaxColumn, ListColumn


class Choices:
    @staticmethod
    def genome_tags():
        return [(t.tag, t.tag) for t in Tag.objects.filter(genome__isnull=False).distinct()]

    @staticmethod
    def organism_tags():
        return [(t.tag, t.tag) for t in Tag.objects.filter(organism__isnull=False).distinct()]


class GenomeFilter:
    column_classes = [SimpleColumn, BinaryColumn, MultipleRelatedColumn, DateRangeColumn, RangeColumn, PercentageRangeColumn, TaxColumn, ListColumn]

    @staticmethod
    def __get_columns() -> dict[str, Column]:
        Columns = [
            SimpleColumn('Organism', lookup_expr='organism__name', render_expr='organism_html'),
            SimpleColumn('Identifier', render_expr='genome_html'),
            SimpleColumn('Old Identifier'),

            BinaryColumn('Representative', lookup_expr='representative__isnull', render_expr='representative_html',
                         choices=[('', 'Both'), ('True', 'True'), ('False', 'False')]),
            BinaryColumn('Restricted', lookup_expr='organism__restricted', choices=[('', 'Both'), ('True', 'True'), ('False', 'False')]),
            BinaryColumn('Contaminated', choices=[('', 'Both'), ('True', 'True'), ('False', 'False')]),

            MultipleRelatedColumn('Genome Tags', lookup_expr='tags', render_expr='tags_html', choices=Choices.genome_tags),
            MultipleRelatedColumn('Organism Tags', lookup_expr='organism__tags', render_expr='organism_tags_html', choices=Choices.organism_tags),

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

            ListColumn('Broad Isolation Environment', id='env_broad', lookup_expr='env_broad_scale', render_expr='env_broad_scale_html'),
            ListColumn('Local Isolation Environment', id='env_local', lookup_expr='env_local_scale', render_expr='env_local_scale_html'),
            ListColumn('Environment Medium', lookup_expr='env_medium', render_expr='env_medium_html'),
            ListColumn('Literature References', lookup_expr='literature_references', render_expr='literature_references_html'),
        ]
        return {f.id: f for f in Columns}

    default_paginate_by = 30
    default_pagination_options = ['All', 10, 20, 30, 50, 100, 500, 1000]

    @classmethod
    def filter_queryset(cls, request, context, active_filters) -> Manager:
        qs = Genome.objects

        for filter in active_filters:
            try:
                qs = filter.filter(qs, request)
            except Exception as e:
                context['error_danger'].append(str(filter) + str(e))

        return qs

    @classmethod
    def filter_view(cls, request):
        context = extract_errors(request, dict(title='Genome table'))

        context['error_info_bottom'].extend([
            'Use <code>Ctrl</code> and/or <code>Shift</code> to select multiple genomes. '
            'Press <code>ESC</code> to deselect all genomes.',
            'Click on genome tags (or right click) to open the context menu.',
            'Click on "Show columns and filters" to show additional columns and use filters.'
        ])

        context['total_unfiltered_count'] = Genome.objects.count()
        context['activate_js'] = [c.activate_js() for c in cls.column_classes]
        context['submit_js'] = [c.submit_js() for c in cls.column_classes]

        all_columns = cls.__get_columns()

        active_columns = extract_data_or(request=request, key='columns', list=True, sep=',',
                                         default=[k for k in settings.DEFAULT_GENOMES_TABLE_COLUMNS if k in all_columns])

        if 'identifier' not in active_columns:
            active_columns = ['identifier'] + active_columns  # ensure that genome identifiers are always shown

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
        qs = cls.order_qs(qs=qs, request=request, columns=all_columns)

        paginate_by = extract_data(request, 'paginate_by')
        if paginate_by == 'All':
            object_list = qs
        else:
            try:
                paginate_by = int(paginate_by)
            except:
                paginate_by = cls.default_paginate_by

            try:
                page = int(extract_data(request, 'page'))
            except:
                page = 1

            paginator = Paginator(qs, paginate_by)
            page_obj = paginator.page(page)
            context['page_obj'] = page_obj
            object_list = page_obj.object_list
            context['paginator'] = paginator

        object_list = AnnotatedGenomeManager.annotate_all(object_list)
        context['object_list'] = object_list

        column_lookups = [f.render_expr for f in active_columns.values()]

        for col in ['restricted', 'contaminated', 'representative']:
            if col not in active_columns and col in column_lookups:
                column_lookups.remove(col)

        try:
            context['table'] = object_list.values_list(*column_lookups)
        except Exception as e:
            context['error_danger'].append(f'Failed to render columns: {column_lookups}: {str(e)}')
            return render(request, 'website/genome_filter.html', context)

        try:
            context['table'] = object_list.values_list(*column_lookups)
        except Exception as e:
            context['error_danger'].append(f'Failed to render columns: {column_lookups}: {str(e)}')
            return render(request, 'website/genome_filter.html', context)

        context['paginated_by'] = paginate_by
        context['pagination_options'] = cls.default_pagination_options
        if paginate_by not in cls.default_pagination_options:
            context['pagination_options'].append(paginate_by)

        return render(request, 'website/genome_filter.html', context)

    @staticmethod
    def order_qs(qs, request, columns: [Column]):
        sort_column = extract_data_or(request=request, key='sort', default='identifier')
        asc = extract_data_or(request=request, key='asc', default='True')
        asc = (asc.lower() == 'true')
        return columns[sort_column].sort(qs=qs, asc=asc)
