from django.db.models.manager import Manager
from django.db.models import Case, When, F, Value, CharField, BooleanField, ExpressionWrapper, Q, Func
from django.db.models.functions import Concat
from django.contrib.postgres.aggregates import StringAgg


class AnnotatedGenomeManager(Manager):
    def get_queryset(self):
        return self.annotate_all(super().get_queryset())

    @classmethod
    def annotate_all(cls, qs: Manager) -> Manager:
        qs = qs.prefetch_related('genomecontent', 'organism', 'organism__taxid')
        qs = cls.annotate_genome_html(qs)
        qs = cls.annotate_organism_html(qs)
        qs = cls.annotate_representative_html(qs)
        qs = cls.annotate_genome_tags_html(qs)
        qs = cls.annotate_organism_tags_html(qs)
        qs = cls.annotate_env_html(qs, lookup_expr='env_broad_scale')
        qs = cls.annotate_env_html(qs, lookup_expr='env_local_scale')
        qs = cls.annotate_env_html(qs, lookup_expr='env_medium')
        return qs

    @staticmethod
    def annotate_genome_html(qs: Manager, *args, **kwargs) -> Manager:
        # F'<span class="genome ogb-tag" data-species="{taxscientificname}">{identifier}</span>'
        return qs.annotate(
            genome_html=Concat(
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
    def annotate_organism_html(qs: Manager, *args, **kwargs) -> Manager:
        # F'<span class="organism ogb-tag" data-species="{taxscientificname}">{name}</span>'
        return qs.annotate(
            organism_html=Concat(
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
    def annotate_representative_html(qs: Manager, *args, **kwargs) -> Manager:
        # 'True' or 'False'
        return qs.annotate(
            representative_html=
            ExpressionWrapper(
                Q(representative__isnull=False),
                output_field=BooleanField()
            )
        )

    @staticmethod
    def annotate_genome_tags_html(qs: Manager, *args, **kwargs) -> Manager:
        # f'<span class="tag ogb-tag" data-tag="{tag}" title="{description}">{tag}</span>'
        return qs.annotate(
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
    def annotate_organism_tags_html(qs: Manager, *args, **kwargs) -> Manager:
        # f'<span class="tag ogb-tag" data-tag="{tag}" title="{description}">{tag}</span>'
        return qs.annotate(
            organism_tags_html=StringAgg(
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

    @staticmethod
    def annotate_env_html(qs: Manager, lookup_expr: str, *args, **kwargs) -> Manager:
        # <span class="badge badge-warning">{env}</span>
        return qs.annotate(
            **{f'{lookup_expr}_html': Case(
                When(**{
                    f'{lookup_expr}__len__gt': 0,
                    'then': Concat(
                        Value('<span class="badge badge-warning">'),
                        Func(F(lookup_expr), Value('</span><span class="badge badge-warning">'), function='array_to_string',
                             output_field=CharField()),
                        Value('</span><span class="badge badge-warning">'),
                    )
                })
            )}
        )
