from django.conf.urls import url
from django.urls import path, re_path
from website.views import *

app_name = 'website'

urlpatterns = [
    # ex: /
    path('', Index.index_view, name='index'),

    # ex: /download
    re_path(r'download/.*$', Download.download_view, name='download'),

    # ex: /members
    path('members', MemberTable.member_list_view, name='members'),
    path('table-load-script/', LoadTableScript.render_script, name='member-table-script'),
    path('table-ajax/', MemberTableAjax.as_view(), name='member-table-ajax'),

    # ex: /strain/{identifier}
    path('strain/<slug:slug>/', StrainDetailView.as_view(), name='strain'),

    # ex: /strain/{name}
    path('member/<str:slug>/', MemberDetailView.as_view(), name='member'),

    # ex: /taxid/{taxid}
    path('taxid/<str:slug>/', TaxIDDetailView.as_view(), name='taxid'),

    # ex: /gene/{name}
    path('gene/<str:slug>/', GeneDetailView.as_view(), name='gene'),

    # ex: /kegg-single/?keggmap={00030}&members={strain1}+{strain2}
    path('kegg/', KeggView.kegg_view, name='kegg'),

    # ex: /trees/?members={strain1}+{strain2}
    path('trees/', Trees.trees, name='trees'),

    # ex: /annotation-search/?annotations={K01626}+{EC:4.4.4.4}&members={strain1}+{strain2}
    path('annotation-search/', AnnotationSearch.annotation_view, name='annotation-search'),
    path('annotation-matrix/', AnnotationSearch.annotation_matrix, name='annotation-matrix'),

    # ex: /blast/?query={fasta}&members={strain1}+{strain2}
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
    path('api/validate-members/', Api.validate_members, name='api-validate-members'),
    path('api/validate-annotations/', Api.validate_annotations, name='api-validate-annotations'),
    path('api/get-kegg-annos/', Api.get_kegg_annos, name='api-get-kegg-annos'),
    path('api/get-anno-description/', Api.get_anno_description, name='api-get-anno-description'),
    path('api/member-identifier-to-species/', Api.member_identifier_to_species,
         name='api-member-identifier-to-species'),
    path('api/annotation-to-type/', Api.annotation_to_type, name='api-annotation-to-type'),
    path('api/dna-feature-viewer/', Api.dna_feature_viewer, name='api-dna-feature-viewer'),
    path('api/get-gene/', Api.get_gene, name='api-get-gene'),
    path('api/get-tree/', Api.get_tree, name='api-get-tree'),
]
