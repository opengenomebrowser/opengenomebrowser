from django.conf.urls import url
from django.views.generic import RedirectView
from django.urls import path, re_path
from website.views import *

app_name = 'website'

urlpatterns = [
    # ex: /
    path('', Home.home_view, name='index'),

    # favicon.ico
    path('favicon.ico', RedirectView.as_view(url='/static/global/customicons/ogb-circle.svg')),

    # ex: /download
    re_path(r'download/.*$', Download.download_view, name='download'),

    # ex: /genomes
    path('genomes', GenomeTable.genome_list_view, name='genomes'),
    path('table-load-script/', LoadTableScript.render_script, name='genome-table-script'),
    path('table-ajax/', GenomeTableAjax.as_view(), name='genome-table-ajax'),

    # ex: /strain/{identifier}
    path('strain/<slug:slug>/', StrainDetailView.as_view(), name='strain'),

    # ex: /strain/{name}
    path('genome/<str:slug>/', GenomeDetailView.as_view(), name='genome'),

    # ex: /taxid/{taxid} and /taxname/{taxscientificname}
    path('taxid/<str:slug>/', TaxIDDetailView.as_view(), name='taxid'),
    path('taxname/<str:slug>/', TaxIDDetailView.redirect_taxname, name='taxname'),

    # ex: /gene/{name}
    path('gene/<str:slug>/', GeneDetailView.as_view(), name='gene'),

    # ex: /annotation/{name}
    path('annotation/<str:slug>/', AnnotationDetailView.as_view(), name='annotation'),

    # ex: /kegg-single/?keggmap={00030}&genomes={strain1}+{strain2}
    path('kegg/', KeggView.kegg_view, name='kegg'),

    # ex: /trees/?genomes={strain1}+{strain2}
    path('trees/', Trees.trees, name='trees'),

    # ex: /compare-genes/?genes={gene 1}+{gene 2}
    path('compare-genes/', CompareGenes.compare, name='compare-genes'),

    # ex: /annotation-search/?annotations={K01626}+{EC:4.4.4.4}&genomes={strain1}+{strain2}
    path('annotation-search/', AnnotationSearch.annotation_view, name='annotation-search'),
    path('annotation-matrix/', AnnotationSearch.annotation_matrix, name='annotation-matrix'),

    # ex: /blast/?query={fasta}&genomes={strain1}+{strain2}
    path('blast/', Blast.blast_view, name='blast'),
    path('blast/submit', Blast.blast_submit, name='blast-submit'),
    # path('api/autocomplete-genome/', Blast.GenomeAutocomplete.as_view(),
    #      name='api-autocomplete-genome'),

    # ex: /api/{...}
    path('api/autocomplete-annotations/', Api.autocomplete_annotations, name='api-autocomplete-annotations'),
    path('api/autocomplete-kegg-map/', Api.autocomplete_kegg_map, name='api-autocomplete-kegg-map'),
    path('api/autocomplete-genome-identifier/', Api.autocomplete_genome_identifiers,
         name='api-autocomplete-genome-identifier'),
    path('api/search-genes/', Api.search_genes, name='api-search-genes'),
    path('api/validate-keggmap/', Api.validate_keggmap, name='api-validate-keggmap'),
    path('api/validate-genomes/', Api.validate_genomes, name='api-validate-genomes'),
    path('api/validate-annotations/', Api.validate_annotations, name='api-validate-annotations'),
    path('api/get-kegg-annos/', Api.get_kegg_annos, name='api-get-kegg-annos'),
    path('api/get-anno-description/', Api.get_anno_description, name='api-get-anno-description'),
    path('api/genome-identifier-to-species/', Api.genome_identifier_to_species,
         name='api-genome-identifier-to-species'),
    path('api/annotation-to-type/', Api.annotation_to_type, name='api-annotation-to-type'),
    path('api/dna-feature-viewer-single/', Api.dna_feature_viewer_single, name='api-dna-feature-viewer'),
    path('api/dna-feature-viewer-multi/', Api.dna_feature_viewer_multi, name='api-dna-feature-viewer'),
    path('api/get-gene/', Api.get_gene, name='api-get-gene'),
    path('api/get-tree/', Api.get_tree, name='api-get-tree'),

    # ex /test-click-menu/
    path('test-click-menu/', ClickMenu.click_view, name='test-click-menu'),

]
