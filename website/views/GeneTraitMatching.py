from html import escape

from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.db import connection

import pandas as pd
from scipy.stats import fisher_exact, boschloo_exact
from statsmodels.stats.multitest import multipletests

from website.models.Annotation import annotation_types

from website.views.GenomeDetailView import dataframe_to_bootstrap_html
from website.views.helpers.extract_errors import extract_errors
from website.views.helpers.magic_string import MagicQueryManager
from website.views.helpers.extract_requests import contains_data, extract_data

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
    :returns: rendered gene_trait_matching.html
    """

    context = extract_errors(request, dict(
        title='Gene trait matching',
        anno_types=annotation_types.values(),
        multiple_testing_methods=multiple_testing_methods,
        # defaults:
        default_anno_type='OL',
        default_alpha=0.1,
        default_multiple_testing_method='fdr_bh'
    ))

    anno_type_valid, alpha_valid, multiple_testing_method, genomes_g1_valid, genomes_g2_valid = False, False, False, False, False

    if contains_data(request, 'anno_type'):
        anno_type_valid = True
        context['default_anno_type'] = extract_data(request, 'anno_type')

    if contains_data(request, 'alpha'):
        alpha_valid = True
        context['default_alpha'] = extract_data(request, 'alpha')

    if contains_data(request, 'multiple_testing_method'):
        multiple_testing_method = True
        context['default_multiple_testing_method'] = extract_data(request, 'multiple_testing_method')

    if contains_data(request, 'g1'):
        qs_g1 = extract_data(request, 'g1', list=True)

        try:
            magic_query_manager_g1 = MagicQueryManager(queries=qs_g1)
            context['magic_query_manager_g1'] = magic_query_manager_g1
            genomes_g1_valid = True
        except Exception as e:
            context['error_danger'].append(str(e))

    if contains_data(request, 'g2'):
        qs_g2 = extract_data(request, 'g2', list=True)

        try:
            magic_query_manager_g2 = MagicQueryManager(queries=qs_g2)
            context['magic_query_manager_g2'] = magic_query_manager_g2
            genomes_g2_valid = True
        except Exception as e:
            context['error_danger'].append(str(e))

    if genomes_g1_valid and genomes_g2_valid:
        g1_identifiers = set(magic_query_manager_g1.all_genomes.values_list('identifier', flat=True))
        g2_identifiers = set(magic_query_manager_g2.all_genomes.values_list('identifier', flat=True))

        intersection = g1_identifiers.intersection(g2_identifiers)
        if len(intersection) > 0:
            context['error_warning'].append(f'The following genomes occur in both lists: {", ".join(intersection)}')
        if len(g1_identifiers) == 0:
            context['error_warning'].append('Group 1 contains no genomes!')
        if len(g2_identifiers) == 0:
            context['error_warning'].append('Group 2 contains no genomes!')

    if all([anno_type_valid, alpha_valid, multiple_testing_method, genomes_g1_valid, genomes_g2_valid]):
        context.update(dict(
            success=len(context['error_warning']) == 0
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
        return HttpResponse(f'Request failed: g1[] incorrect. {e}')

    qs_g2 = set(request.POST.getlist('g2[]'))
    try:
        magic_query_manager_g2 = MagicQueryManager(qs_g2)
    except Exception as e:
        return HttpResponse(f'Request failed: g2[] incorrect. {e}')

    anno_type = request.POST.get('anno_type')
    alpha = float(request.POST.get('alpha'))
    multiple_testing_method = request.POST.get('multiple_testing_method')

    try:
        gtm_df = gtm(
            g1=set(magic_query_manager_g1.all_genomes.values_list('identifier', flat=True)),
            g2=set(magic_query_manager_g2.all_genomes.values_list('identifier', flat=True)),
            anno_type=anno_type, alpha=alpha, multiple_testing_method=multiple_testing_method)
    except Exception as e:
        return JsonResponse(dict(success='false', message=str(e)), status=500)

    if len(gtm_df) == 0:
        return JsonResponse(dict(success='false', message='Found no significantly different annotations.'), status=409)

    return JsonResponse(to_json(gtm_df=gtm_df))


def gtm(
        g1: {str},
        g2: {str},
        anno_type: str = 'OL',
        method: str = 'boschloo',
        alpha: float = 0.25,
        multiple_testing_method: str = 'fdr_bh'
) -> pd.DataFrame:
    """
    Calculate gene-trait-matching analysis. Find proteins hat are significantly over- or underrepresented in one group of genomes.

    :param g1: First group of genomes
    :param g2: Second group of genomes
    :param anno_type: Annotation type to be used to link proteins between genomes
    :param method: test to be applied, either 'fisher' or 'boschloo'
    :param alpha: Alpha / FWER (family-wise error rate)
    :param multiple_testing_method: See https://www.statsmodels.org/dev/generated/statsmodels.stats.multitest.multipletests.html
    :return: Table of proteins that are significantly over- or underrepresented.
    """
    intersection = set.intersection(g1, g2)
    all_g = set.union(g1, g2)
    assert len(intersection) == 0, f'The following genomes occur in both lists: {", ".join(intersection)}'
    assert len(g1) > 0, 'Group 1 contains no genomes.'
    assert len(g2) > 0, 'Group 2 contains no genomes.'

    if method == 'fisher':
        test_fn = lambda r: fisher_exact([
            [r.g1, r.g2],
            [r.not_g1, r.not_g2]
        ])[1]
    elif method == 'boschloo':
        # column sums must be fixed!
        test_fn = lambda r: boschloo_exact([
            [r.g1, r.g2],
            [r.not_g1, r.not_g2]
        ]).pvalue
    else:
        raise AssertionError(f"method must be either 'fisher' or 'boschloo'. {method=}")

    with connection.cursor() as cursor:
        cursor.execute(
            '''
            SELECT * FROM (
                SELECT "name", "description",
                    COUNT(genomecontent_id) FILTER ( WHERE genomecontent_id IN %s ) as g1,
                    COUNT(genomecontent_id) FILTER ( WHERE genomecontent_id IN %s ) as g2
                FROM website_genomecontent_annotations
                     LEFT OUTER JOIN website_annotation ON ("name" = "annotation_id")
                WHERE "anno_type" = %s AND "genomecontent_id" IN %s
                GROUP BY "name"
            ) AS foo WHERE NOT (g1 = %s AND g2 = %s);
            ''',
            [tuple(g1), tuple(g2), anno_type, tuple(all_g), len(g1), len(g2)]
        )

        annos = pd.DataFrame(list(cursor.fetchall()), columns=['annotation', 'description', 'g1', 'g2'])

    assert len(annos) > 0, f'No annotations found for anno_type={anno_type}'

    # get unique combinations of g1 and g2 to calculate fewer tests:
    gtm_df = annos[['g1', 'g2']].drop_duplicates().reset_index(drop=True)
    gtm_df['not_g1'] = len(g1) - gtm_df['g1']
    gtm_df['not_g2'] = len(g2) - gtm_df['g2']
    gtm_df['pvalue'] = gtm_df.apply(test_fn, axis=1)
    gtm_df.drop(['not_g1', 'not_g2'], axis=1, inplace=True)

    # most significant first
    gtm_df.sort_values(by='pvalue', inplace=True)

    # apply multiple testing correction
    reject, pvals_corrected, alphac_sidak, alphac_bonf = multipletests(
        gtm_df['pvalue'], is_sorted=True,
        alpha=alpha, method=multiple_testing_method
    )
    gtm_df['p_corrected'] = pvals_corrected
    gtm_df['reject'] = reject

    # remove rows where corrected p-value is 1
    gtm_df = gtm_df[gtm_df['p_corrected'] < 1]

    # format in percentage
    gtm_df['g1_%'] = gtm_df['g1'] / len(g1)
    gtm_df['g2_%'] = gtm_df['g2'] / len(g2)

    # perform left outer join
    gtm_df = pd.merge(gtm_df, annos, on=['g1', 'g2'], how='left')

    # add parameters of gtm to pandas dataframe attributes
    gtm_df.attrs.update({
        'g1': g1, 'g2': g2,
        'anno_type': anno_type, 'method': method,
        'multiple_testing_method': multiple_testing_method, 'alpha': alpha
    })

    # columns: ['g1', 'g2', 'pvalue', 'p_corrected', 'reject', 'g1_%', 'g2_%', 'annotation', 'description']
    return gtm_df


def prettify(gtm_df: pd.DataFrame) -> pd.DataFrame:
    assert list(gtm_df.columns) == ['g1', 'g2', 'pvalue', 'p_corrected', 'reject', 'g1_%', 'g2_%', 'annotation', 'description'], \
        f'Columns do not match. Got: {list(gtm_df.columns)}'
    for attr in ['g1', 'g2', 'anno_type', 'method', 'multiple_testing_method', 'alpha']:
        assert attr in gtm_df.attrs, f'Dataframe is missing attr: {attr}'

    anno_type = gtm_df.attrs['anno_type']
    multiple_testing_method = gtm_df.attrs['multiple_testing_method']
    method = gtm_df.attrs['method']
    len_g1 = len(gtm_df.attrs['g1'])
    len_g2 = len(gtm_df.attrs['g2'])

    html = lambda \
        row: f"<div class='annotation ogb-tag' data-annotype='{anno_type}' title='{escape(row['description'])}'>{escape(row['annotation'])}</div>"

    gtm_df['annotation_html'] = gtm_df.apply(html, axis=1)
    gtm_df['g1'] = gtm_df['g1'].apply(lambda x: f'{x}/{len_g1}')
    gtm_df['g2'] = gtm_df['g2'].apply(lambda x: f'{x}/{len_g2}')
    gtm_df[['g1_%', 'g2_%']] = gtm_df[['g1_%', 'g2_%']].applymap(lambda x: f'{x * 100:.3g}%')
    gtm_df[['pvalue', 'p_corrected']] = gtm_df[['pvalue', 'p_corrected']].applymap('{:.2g}'.format)  # 2 significant figures

    method_str = f'pvalue ({method.capitalize()}\'s test)'
    gtm_df = gtm_df[[
        'annotation', 'description', 'annotation_html', 'g1_%', 'g2_%', 'g1', 'g2', 'pvalue', 'p_corrected', 'reject'
    ]]
    gtm_df.columns = [
        '_annotation', 'Description', 'Annotation', 'Group 1 [%]', 'Group 2 [%]', 'Group 1', 'Group 2', method_str, 'qvalue (corrected)', 'reject H0'
    ]
    return gtm_df


def to_html(gtm_df: pd.DataFrame) -> str:
    gtm_df = prettify(gtm_df)
    return dataframe_to_bootstrap_html(gtm_df, index=False, table_id='gene-trait-matching-table')


def to_json(gtm_df: pd.DataFrame) -> dict:
    gtm_df = prettify(gtm_df)

    json_response = dict(
        dataset=gtm_df.values.tolist(),
        columns=[dict(title=c) for c in gtm_df.columns]
    )

    return json_response
