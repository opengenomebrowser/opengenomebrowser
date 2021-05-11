from django_datatables_view.base_datatable_view import BaseDatatableView
from django.db.models import Q
from django.contrib.postgres.aggregates.general import ArrayAgg

from website.models import Genome


class GenomeTableAjax(BaseDatatableView):
    # The model we're going to show
    model = Genome

    # set max limit of records returned, this is used to protect our site if someone tries to attack our site
    # and make it return huge amount of data
    max_display_length = 2000

    def render_column(self, row: Genome, column: str):
        if column == 'representative':
            return 'True' if row.is_representative else 'False'
        if column == 'genome_tags':
            return ' '.join(F'<span data-tag="{tag}">{tag}</span>' for tag in row.genome_tags if tag)
        if column == 'organism_tags':
            return ' '.join(F'<span data-tag="{tag}">{tag}</span>' for tag in row.organism_tags if tag)
        if column == 'env_broad_scale':
            return ' '.join(F'<span class="badge badge-warning">{env}</span>' for env in row.env_broad_scale if env)
        if column == 'env_local_scale':
            return ' '.join(F'<span class="badge badge-warning">{env}</span>' for env in row.env_local_scale if env)
        if column == 'env_medium':
            return ' '.join(F'<span class="badge badge-warning">{env}</span>' for env in row.env_medium if env)
        if column == 'literature_references':
            return ' '.join(F'<a class="badge badge-info">{ref.get("name", "no name")}</a>' for ref in row.literature_references if ref)
        else:
            return super(GenomeTableAjax, self).render_column(row, column)

    def get_initial_queryset(self):
        if not self.model:
            raise NotImplementedError("Need to provide a model or implement get_initial_queryset!")
        qs = self.model.objects.annotate(
            genome_tags=ArrayAgg('tags__tag', distinct=True),
            organism_tags=ArrayAgg('organism__tags__tag', distinct=True)
        ) \
            .all() \
            .prefetch_related('organism') \
            .prefetch_related('organism__taxid')
        return qs

    def filter_queryset(self, qs):
        """ If search['value'] is provided then filter all searchable columns using filter_method (istartswith
            by default).

            Automatic filtering only works for Datatables 1.10+. For older versions override this method
        """

        columns = self._columns
        if not self.pre_camel_case_notation:
            # get global search value
            search = self._querydict.get('search[value]', None)
            q = Q()
            filter_method = self.get_filter_method()
            for col_no, col in enumerate(self.columns_data):
                # apply global search to all searchable columns
                if search and col['searchable']:
                    # cannot search binary fields or tags
                    if not columns[col_no] in ['representative', 'contaminated', 'organism.restricted']:
                        q |= Q(**{F"{columns[col_no].replace('.', '__')}__{filter_method}": search})

                # column specific filter
                if col['search.value']:
                    col['search.value'] = col['search.value'].replace('\\', '')  # this happens if there is a . in the string.
                    colname = col['name']

                    ## CUSTOM FILTERS
                    if colname == 'representative':
                        if col['search.value'] == "True":
                            qs = qs.filter(representative__isnull=False)
                        else:
                            qs = qs.filter(representative__isnull=True)
                    elif colname == "genome_tags":
                        qs = qs.filter(tags__tag__in=col['search.value'].split("|"))
                    elif colname == "organism_tags":
                        qs = qs.filter(organism__tags__tag__in=col['search.value'].split("|"))
                    elif colname.endswith("_date"):
                        if col['search.value'].startswith("-yadcf_delim"):
                            range = ["0001-01-01", col['search.value'][-10:]]
                        elif col['search.value'].endswith("yadcf_delim-"):
                            range = [col['search.value'][:10], "9000-12-30"]
                        else:
                            range = [col['search.value'][:10], col['search.value'][-10:]]
                        qs = qs.filter(**{'{0}__{1}'.format(columns[col_no].replace('.', '__'), 'range'): range})

                    else:
                        # DEFAULT BEHAVIOUR
                        qs = qs.filter(**{
                            '{0}__{1}'.format(columns[col_no].replace('.', '__'), filter_method): col['search.value']})
            qs = qs.filter(q)

        return qs
