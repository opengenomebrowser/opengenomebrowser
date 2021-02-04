from django.shortcuts import render, HttpResponse
from django.db.models import Q, Count
from django.http import JsonResponse

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from statsmodels.stats.multitest import multipletests

from website.models import Genome, Gene, GenomeContent
from website.models.Annotation import Annotation, annotation_types

from .GenomeDetailView import dataframe_to_bootstrap_html
from .helpers.magic_string import MagicQueryManager, MagicError

multiple_testing_methods = {
    'bonferroni': 'Bonferroni: one-step correction',
    'sidak': 'Sidak: one-step correction',
    'holm-sidak': 'Holm-Sidak: step down method using Sidak adjustments',
    'holm': 'Holm: step-down method using Bonferroni adjustments',
    'simes-hochberg': 'Simes-Hochberg : step-up method (independent)',
    'hommel': 'Hommel: closed method based on Simes tests (non-negative)',
    'fdr_bh': 'Benjamini/Hochberg (non-negative)',
    'fdr_by': 'Benjamini/Yekutieli (negative)',
    'fdr_tsbh': 'fdr_tsbh: two stage fdr correction (non-negative)',
    'fdr_tsbky': 'two stage: fdr correction (non-negative)'
}


def gtm_view(request):
    """
    This function loads the page /gene-trait-matching/

    :param request: may contain: ['g1[]', 'g2[]', 'alpha', 'anno_type', 'multiple_testing_method']
    :return: rendered gene_trait_matching.html
    """

    context = dict(
        title='Gene trait matching',
        anno_types=annotation_types.values(),
        multiple_testing_methods=multiple_testing_methods,
        # defaults:
        default_anno_type='OL',
        default_alpha=0.1,
        default_multiple_testing_method='fdr_bh'
    )

    anno_type_valid, alpha_valid, multiple_testing_method, genomes_g1_valid, genomes_g2_valid = False, False, False, False, False

    if 'anno_type' in request.GET:
        anno_type_valid = True
        context['default_anno_type'] = request.GET['anno_type']

    if 'alpha' in request.GET:
        alpha_valid = True
        context['default_alpha'] = request.GET['alpha']

    if 'multiple_testing_method' in request.GET:
        multiple_testing_method = True
        context['default_multiple_testing_method'] = request.GET['multiple_testing_method']

    if 'g1' in request.GET:
        qs_g1 = set(request.GET['g1'].split(' '))

        try:
            magic_query_manager_g1 = MagicQueryManager(queries=qs_g1)
            genome_to_species_g1 = magic_query_manager_g1.genome_to_species()
            context['magic_query_manager_g1'] = magic_query_manager_g1
            context['genome_to_species_g1'] = genome_to_species_g1
            genomes_g1_valid = True
        except Exception as e:
            context['error_danger'] = str(e)

    if 'g2' in request.GET:
        qs_g2 = set(request.GET['g2'].split(' '))

        try:
            magic_query_manager_g2 = MagicQueryManager(queries=qs_g2)
            genome_to_species_g2 = magic_query_manager_g2.genome_to_species()
            context['magic_query_manager_g2'] = magic_query_manager_g2
            context['genome_to_species_g2'] = genome_to_species_g2
            genomes_g2_valid = True
        except Exception as e:
            context['error_danger'] = str(e)

    if genomes_g1_valid and genomes_g2_valid:
        g1_identifiers = set(magic_query_manager_g1.all_genomes.values_list('identifier', flat=True))
        g2_identifiers = set(magic_query_manager_g2.all_genomes.values_list('identifier', flat=True))

        intersection = g1_identifiers.intersection(g2_identifiers)
        if len(intersection) > 0:
            context['error_warning'] = F'The following genomes occur in both lists: {", ".join(intersection)}'
        if len(g1_identifiers) == 0:
            context['error_warning'] = 'Group 1 contains no genomes!'
        if len(g2_identifiers) == 0:
            context['error_warning'] = 'Group 2 contains no genomes!'

    if all([anno_type_valid, alpha_valid, multiple_testing_method, genomes_g1_valid, genomes_g2_valid]):
        context.update(dict(
            success='error_warning' not in context
        ))

    return render(request, 'website/gene_trait_matching.html', context)


def gtm_table(request):
    """
    This function is activated in gene_trait_matching.html. The getJSON-request must contain the parameters for the gtm-function below.

    :param request: must contain: ['g1[]', 'g2[]', 'alpha', 'anno_type', 'multiple_testing_method']
    :return: gene-trait-matching-table in json format, as required by DataTables.
    """
    context = {}

    # check input
    for input in ['g1[]', 'g2[]', 'alpha', 'anno_type', 'multiple_testing_method']:
        if input not in request.POST:
            return HttpResponse(f'Request failed! Please POST {input}.')

    qs_g1 = set(request.POST.getlist('g1[]'))
    try:
        magic_query_manager_g1 = MagicQueryManager(qs_g1)
    except Exception as e:
        return HttpResponse(F'Request failed: g1[] incorrect. {e}')

    qs_g2 = set(request.POST.getlist('g2[]'))
    try:
        magic_query_manager_g2 = MagicQueryManager(qs_g2)
    except Exception as e:
        return HttpResponse(F'Request failed: g2[] incorrect. {e}')

    anno_type = request.POST.get('anno_type')
    alpha = float(request.POST.get('alpha'))
    multiple_testing_method = request.POST.get('multiple_testing_method')

    gtm_df = gtm(g1=magic_query_manager_g1.all_genomes, g2=magic_query_manager_g2.all_genomes,
                 anno_type=anno_type, alpha=alpha, multiple_testing_method=multiple_testing_method)

    json_response = to_json(gtm_df=gtm_df, anno_type=anno_type)

    return JsonResponse(json_response)


def gtm(g1: [Genome], g2: [Genome], anno_type='OL', alpha=0.25, multiple_testing_method='fdr_bh') -> pd.DataFrame:
    """
    Calculate gene-trait-matching analysis. Find proteins hat are significantly over- or underrepresented in one group of genomes.

    :param g1: First group of genomes
    :param g2: Second group of genomes
    :param anno_type: Annotation type to be used to link proteins between genomes
    :param alpha: Alpha / FWER (family-wise error rate)
    :param multiple_testing_method: See https://www.statsmodels.org/dev/generated/statsmodels.stats.multitest.multipletests.html
    :return: Table of proteins that are significantly over- or underrepresented.
    """
    g1 = g1.values_list('identifier', flat=True)
    g2 = g2.values_list('identifier', flat=True)

    intersection = g1.intersection(g2)

    assert len(intersection) == 0, F'The following genomes occur in both lists: {", ".join(intersection)}'
    assert len(g1) > 0, 'Group 1 contains no genomes.'
    assert len(g2) > 0, 'Group 2 contains no genomes.'

    annos_qs = Annotation.objects \
        .annotate(g1=Count('genomecontent', filter=Q(genomecontent__in=g1))) \
        .annotate(g2=Count('genomecontent', filter=Q(genomecontent__in=g2))) \
        .filter(anno_type=anno_type)

    annos = annos_qs.all().values_list('name', 'description', 'g1', 'g2')

    annos = pd.DataFrame(list(annos), columns=['annotation', 'description', 'g1', 'g2'])

    # only keep annotations which are covered
    annos = annos.loc[np.where(annos['g1'] + annos['g2'] > 0)]

    n_rows = len(annos)

    # get unique combinations of g1 and g2 to calculate fewer fisher's tests:
    fisher_df = annos.groupby(['g1', 'g2']).size().reset_index()
    fisher_df.drop([0], axis=1, inplace=True)
    fisher_df['not_g1'] = len(g1) - fisher_df['g1']
    fisher_df['not_g2'] = len(g2) - fisher_df['g2']
    fisher_df['p_fisher_exact'] = fisher_df.apply(
        lambda r: fisher_exact([
            [r.g1, r.not_g1],
            [r.g2, r.not_g2]
        ])[1],
        axis=1
    )
    fisher_df.drop(['not_g1', 'not_g2'], axis=1, inplace=True)

    # perform left outer join
    annos = pd.merge(annos, fisher_df, on=['g1', 'g2'], how='left')

    # sort by highest fisher's test
    annos.sort_values(by='p_fisher_exact', inplace=True)

    # apply multiple testing correction
    reject, pvals_corrected, alphac_sidak, alphac_bonf = multipletests(
        annos['p_fisher_exact'], is_sorted=True,
        alpha=alpha, method=multiple_testing_method
    )
    annos['p_corrected'] = pvals_corrected
    annos['reject'] = reject
    assert len(annos) == n_rows, F'wtf?{n_rows} -> {len(annos)}'

    # remove rows where corrected p-value is 1
    annos = annos[annos['p_corrected'] < 1]

    return annos


def prettify(gtm_df: pd.DataFrame, anno_type: str) -> pd.DataFrame:
    assert list(gtm_df.columns) == ['annotation', 'description', 'g1', 'g2', 'p_fisher_exact', 'p_corrected', 'reject']

    def html(row):
        return F'<div class="annotation ogb-tag" data-annotype="{anno_type}" title="{row["description"]}">{row["annotation"]}</div>'

    gtm_df['annotation'] = gtm_df.apply(lambda row: html(row), axis=1)
    gtm_df.drop('description', axis=1, inplace=True)

    gtm_df.columns = ['Annotation', 'Group 1', 'Group 2', 'pvalue (Fisher\'s test)', 'qvalue (corrected)', 'reject H0']

    return gtm_df


def to_html(gtm_df: pd.DataFrame, anno_type: str) -> str:
    gtm_df = prettify(gtm_df, anno_type)
    return dataframe_to_bootstrap_html(gtm_df, index=False, table_id='gene-trait-matching-table')


def to_json(gtm_df: pd.DataFrame, anno_type: str) -> dict:
    gtm_df = prettify(gtm_df, anno_type)

    json_response = dict(
        dataset=gtm_df.values.tolist(),
        columns=[dict(title=c) for c in gtm_df.columns]
    )

    return json_response
