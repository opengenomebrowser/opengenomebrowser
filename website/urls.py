from django.urls import path, re_path

from website.views import *

app_name = 'website'

urlpatterns = [
    # ex: /
    path('', Home.home_view, name='index'),

    # ex: /files_html and /files_json
    re_path(r'files_html/.*$', Files.files_html, name='files-html'),
    re_path(r'files_json/.*$', Files.files_json, name='files-json'),
    re_path(r'files_cache/.*$', Files.files_cache, name='files-cache'),

    # ex: /genomes
    path('genomes/', GenomeFilter.filter_view, name='genomes'),

    # ex: /organism/{identifier}
    path('organism/<str:slug>/', OrganismDetailView.as_view(), name='organism'),

    # ex: /genome/{name}
    path('genome/<str:slug>/', GenomeDetailView.as_view(), name='genome'),

    # ex: /taxid/{taxid} and /taxname/{taxscientificname}
    path('taxid/<str:slug>/', TaxIDDetailView.as_view(), name='taxid'),
    path('taxname/<str:slug>/', TaxIDDetailView.redirect_taxname, name='taxname'),

    # ex: /gene/{name}
    path('gene/<str:slug>/', GeneDetailView.as_view(), name='gene'),

    # ex: /annotation/{name}
    path('annotations/', AnnotationFilter.filter_view, name='annotation-filter'),
    path('annotation/<str:slug>/', AnnotationDetailView.as_view(), name='annotation'),

    # ex: /annotation-search/?annotations={K01626}+{EC:4.4.4.4}&genomes={organism1}+{organism2}
    path('annotation-search/', AnnotationSearch.annotation_view, name='annotation-search'),
    path('annotation-search-matrix/', AnnotationSearch.matrix, name='annotation-search-matrix'),

    # ex: /pathway/?map_slug={kegg-map-00400}&genomes={organism1}+{organism2}
    path('pathway/', PathwayView.pathway_view, name='pathway'),

    # ex: /trees/?genomes={organism1}+{organism2}
    path('trees/', Trees.trees, name='trees'),

    # ex: /trees/?genomes={organism1}+{organism2}
    path('dotplot/', Dotplot.dotplot_view, name='dotplot'),

    # ex: /compare-genes/?genes={gene 1}+{gene 2}
    path('compare-genes/', CompareGenes.compare, name='compare-genes'),

    # ex: /gene-trait-matching/?g1={organism1}+{organism2}&g2={organism3}+{organism4}
    path('gene-trait-matching/', GeneTraitMatching.gtm_view, name='gene-trait-matching'),
    path('gene-trait-matching-table/', GeneTraitMatching.gtm_table, name='gene-trait-matching-table'),

    # ex: /blast/?query={fasta}&genomes={organism1}+{organism2}
    path('blast/', Blast.blast_view, name='blast'),
    path('blast/submit', Blast.blast_submit, name='blast-submit'),

    # ex: /downloader
    path('downloader/', Downloader.downloader_view, name='downloader'),
    path('downloader/submit/', Downloader.downloader_submit, name='downloader-submit'),
    path('downloader/is_loaded/', Downloader.downloader_is_loaded, name='downloader-is-loaded'),

    # ex: /api/{...}
    path('api/autocomplete-annotations/', Api.autocomplete_annotations, name='api-autocomplete-annotations'),
    path('api/autocomplete-pathway/', Api.autocomplete_pathway, name='api-autocomplete-pathway'),
    path('api/autocomplete-genomes/', Api.autocomplete_genomes, name='api-autocomplete-genomes'),
    path('api/autocomplete-genes/', Api.autocomplete_genes, name='api-autocomplete-genes'),
    path('api/autocomplete-genes/', Api.autocomplete_genes, name='api-autocomplete-genes'),
    path('api/validate-pathwaymap/', Api.validate_pathwaymap, name='api-validate-pathwaymap'),
    path('api/validate-genomes/', Api.validate_genomes, name='api-validate-genomes'),
    path('api/validate-genes/', Api.validate_genes, name='api-validate-genes'),
    path('api/validate-annotations/', Api.validate_annotations, name='api-validate-annotations'),
    path('api/genome-identifier-to-species/', Api.genome_identifier_to_species, name='api-genome-identifier-to-species'),
    path('api/annotation-to-type/', Api.annotation_to_type, name='api-annotation-to-type'),
    path('api/dna-feature-viewer-single/', Api.dna_feature_viewer_single, name='api-dna-feature-viewer'),
    path('api/dna-feature-viewer-multi/', Api.dna_feature_viewer_multi, name='api-dna-feature-viewer'),
    path('api/align/', Api.align, name='api-align'),
    path('api/get-gene/', Api.get_gene, name='api-get-gene'),
    path('api/get-tree/', Api.get_tree, name='api-get-tree'),
    path('api/reload-orthofinder/', Api.reload_orthofinder, name='api-reload-orthofinder'),
    path('api/get-dotplot/', get_dotplot, name='api-get-dotplot'),
    path('api/get-dotplot-annotations/', get_dotplot_annotations, name='api-get-dotplot-annotations'),
    path('api/score-pathway-maps/', PathwayView.score_pathway_maps, name='api-score-pathway-maps'),

    # ex /test-click-menu/
    path('test-click-menu/', ClickMenu.click_view, name='test-click-menu'),
]
