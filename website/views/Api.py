from django.shortcuts import HttpResponse
from django.http import JsonResponse
import json
import os
from django.http import HttpResponseBadRequest

from OpenGenomeBrowser import settings
from website.models.Annotation import Annotation
from website.models import Genome, Member, KeggMap, Gene, TaxID, ANI
from website.models.Tree import TaxIdTree, AniTree, OrthofinderTree, TreeNotDoneError
from django.db.models.functions import Concat
from django.db.models import CharField, Value as V

from lib.gene_loci_comparison.gene_loci_comparison import GraphicRecordLocus
from bokeh.embed import components


def err(error_message):
    print(error_message)
    return JsonResponse(dict(status='false', message=error_message), status=500)


class Api:
    @staticmethod
    def member_identifier_to_species(request):
        if not request.GET:
            return err('did not receive valid JSON')

        if not ('members[]' in request.GET):
            return err(F"missing parameter 'members[]'. Got: {request.GET.keys()}")

        members = set(request.GET.getlist('members[]'))

        member_to_species = Member.objects.filter(identifier__in=members).prefetch_related('strain', 'strain__taxid') \
            .values('identifier', 'strain__taxid', 'strain__taxid__taxscientificname')

        member_to_species = {m['identifier']:
            dict(
                taxid=m['strain__taxid'],
                sciname=m['strain__taxid__taxscientificname']
            ) for m in member_to_species}

        if len(member_to_species) != len(members):
            missing = set(members).difference(set(member_to_species.keys()))
            return err(F"could not find genome for members='{missing}'")

        return JsonResponse(member_to_species)

    @staticmethod
    def annotation_to_type(request):
        if not request.GET:
            return err('did not receive valid JSON')

        if not ('annotations[]' in request.GET):
            return err(F"missing parameter 'annotations[]'. Got: {request.GET.keys()}")

        annotations = request.GET.getlist('annotations[]')
        try:
            annotations = [Annotation.objects.get(name=anno) for anno in annotations]
        except Annotation.DoesNotExist:
            return err("One or more annotations doesn't mach any type.")

        annotation_to_type = {anno.name:
            dict(
                anno_type=anno.anno_type,
                description=anno.description
            )
            for anno in annotations}

        return JsonResponse(annotation_to_type)

    @staticmethod
    def autocomplete_kegg_map(request):
        # http://flaviusim.com/blog/AJAX-Autocomplete-Search-with-Django-and-jQuery/
        if not 'term' in request.GET:
            return err('"term" not in request.GET')

        q = request.GET.get('term', '')

        # create 'synthetic' charfield
        # https://docs.djangoproject.com/en/2.2/ref/models/database-functions/#concat
        all_keggmaps = KeggMap.objects.annotate(map_id_and_name=Concat(
            'map_id', V(' : '), 'map_name',
            output_field=CharField()
        )).all()

        maps = all_keggmaps.filter(map_id_and_name__icontains=q)[:20]  # return 20 results
        results = []
        for map in maps:
            results.append({
                'label': F"{map.map_id_and_name} ({map.map_name})",
                'value': map.map_id_and_name
            })
        data = json.dumps(results)
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)

    @staticmethod
    def autocomplete_annotations(request):
        # http://flaviusim.com/blog/AJAX-Autocomplete-Search-with-Django-and-jQuery/
        if not 'term' in request.GET:
            return err('"term" not in request.GET')

        q = request.GET.get('term', '')

        # create 'synthetic' charfield
        # https://docs.djangoproject.com/en/2.2/ref/models/database-functions/#concat
        try:
            annotations = Annotation.objects.filter(name__istartswith=q)[:20]
        except Annotation.DoesNotExist:
            annotations = []

        results = []
        for annotation in annotations:
            results.append({
                'label': F"{annotation.name} ({Annotation.get_auto_description(annotation.name)})",
                'value': annotation.name
            })
        data = json.dumps(results)
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)

    @staticmethod
    def search_genes(request):
        # http://flaviusim.com/blog/AJAX-Autocomplete-Search-with-Django-and-jQuery/
        term = request.GET.get('term', None)

        genome = request.GET.get('genome', None)

        if term is None and genome is None:
            return err('"term" and "genome" are not in request.GET')

        print(genome, term)

        if genome:
            genes = Gene.objects.filter(genome=genome, identifier__icontains=term if term else '').order_by('identifier')[:10]
        else:
            genes = Gene.objects.filter(identifier__istartswith=term).order_by('identifier')[:10]

        results = [gene.identifier for gene in genes]

        data = json.dumps(results)
        mimetype = 'application/json'
        print(results)
        return HttpResponse(data, mimetype)

    @staticmethod
    def autocomplete_genome_identifiers(request):
        # http://flaviusim.com/blog/AJAX-Autocomplete-Search-with-Django-and-jQuery/
        if not 'term' in request.GET:
            return err('"term" not in request.GET')
        q = request.GET.get('term', '')
        genomes = Genome.objects.filter(identifier__icontains=q)[:20]
        genomes.prefetch_related('strain__taxid')
        results = []
        for genome in genomes:
            results.append({
                'label': F"{genome.identifier} ({genome.strain.taxid.taxscientificname})",
                'value': genome.identifier
            })
        data = json.dumps(results)
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)

    @staticmethod
    def validate_annotations(request):
        """
        Test if annotations exist in the database.
        """
        if not request.GET:
            return err('did not receive valid JSON')

        if not 'annotations[]' in request.GET:
            return err('did not receive annotations[]')

        annotations = set(request.GET.getlist('annotations[]'))

        try:
            annotations = [Annotation.objects.get(name=anno) for anno in annotations]
            success = True
        except Annotation.DoesNotExist:
            success = False

        return JsonResponse(dict(success=success))

    @staticmethod
    def validate_keggmap(request):
        """
        Test if map_id exist in the database.
        """
        if not request.GET:
            return err('did not receive valid JSON')

        if not 'map_id' in request.GET:
            return err('did not receive map_id')

        success = KeggMap.objects.filter(map_id=request.GET['map_id']).exists()

        return JsonResponse(dict(success=success))

    @staticmethod
    def validate_members(request):
        """
        Test if members exist in the database.
        """
        if not request.GET:
            return err('did not receive valid JSON')

        if not 'members[]' in request.GET:
            return err('did not receive members[]')

        query_members = set(request.GET.getlist('members[]'))
        found_members = set(Member.objects.filter(identifier__in=query_members).values_list('identifier', flat=True))

        success = query_members == found_members

        return JsonResponse(dict(success=success))

    @staticmethod
    def get_kegg_annos(request):
        """
        Get the annotations a strain has for a given KEGG map.

        Queries: map_id, members

        Returns: {k: ['K0000', ...], r: [], ec: []}
        """
        if not request.GET:
            return err('did not receive valid JSON')

        if not ('map_id' and 'members[]' in request.GET):
            return err(F"missing parameters. required: 'map_id' and 'members[]'. Got: {request.GET.keys()}")

        map_id = request.GET['map_id']
        members = request.GET.getlist('members[]')

        strain_to_annotations = {}

        map_annos = Annotation.objects.filter(keggmap=map_id)

        for identifier in members:
            if not Genome.objects.filter(pk=identifier).exists():
                return err(F"could not find genome for member='{identifier}'")

            strain_to_annotations[identifier] = dict(
                k=list(map_annos.filter(anno_type='KG', genome=identifier).values_list(flat=True)),
                r=list(map_annos.filter(anno_type='KR', genome=identifier).values_list(flat=True)),
                ec=list(map_annos.filter(anno_type='EC', genome=identifier).values_list(flat=True))
            )

        return JsonResponse(strain_to_annotations)

    @staticmethod
    def get_anno_description(request):
        """
        Get the description of an annotation.

        Query: ['K0000', ...]

        Returns {'K0000': 'Histidine decarboxylase', ...}
        """

        if not request.GET:
            return err('did not receive valid JSON')

        if not ('annotations[]' in request.GET):
            return err(F"missing parameters. required: 'annotations[]'. Got: {request.GET.keys()}")

        annotations = set(request.GET.getlist('annotations[]'))

        try:
            anno_to_description = {anno: Annotation.get_auto_description(anno) for anno in annotations}
        except Annotation.DoesNotExist:
            return err('One or more anntations could not be found.')

        return JsonResponse(anno_to_description)

    @staticmethod
    def dna_feature_viewer(request):
        """
        Get dna_feature_viewer bokeh around gene_identifier.

        Query: gene_identifier = "strain3_000345"

        Returns bokeh script and div

        Todo: Span around gene_locus
        """

        if not request.GET:
            return err('did not receive valid JSON')

        if not ('gene_identifier' in request.GET):
            return err(F"missing parameters. required: 'gene_identifier'. Got: {request.GET.keys()}")

        gene_identifier = request.GET.get('gene_identifier')

        g = Gene.objects.get(identifier=gene_identifier)

        graphic_record = GraphicRecordLocus(gbk_file=g.genome.member.cds_gbk(relative=False), locus_tag=gene_identifier, span=30000)

        graphic_record.colorize_graphic_record({gene_identifier: '#1984ff'}, strict=False, default_color='#ffffff')

        plot = graphic_record.plot_with_bokeh(figure_width=11.4,  # width of .container divs
                                              figure_height='auto',
                                              viewspan=3000)

        script, plot_div = components(plot)
        script = script[33:-10]  # remove <script type="text/javascript"> and </script>

        return JsonResponse(dict(script=script, plot_div=plot_div))

    @staticmethod
    def get_gene(request):
        """
        Get information about a gene.

        Query: gene_identifier = "strain3_000345"

        Returns JSON
        """

        if not request.GET:
            return err('did not receive valid JSON')

        if not ('gene_identifier' in request.GET):
            return err(F"missing parameters. required: 'gene_identifier'. Got: {request.GET.keys()}")

        gene_identifier = request.GET.get('gene_identifier')

        g = Gene.objects.get(identifier=gene_identifier)

        return JsonResponse(dict(
            member=g.genome.identifier,
            member_html=g.genome.member.member_html,
            identifier=g.identifier,
            annotations=[
                dict(
                    name=annotation.name,
                    anno_type=annotation.anno_type,
                    anno_type_verbose=annotation.anno_type_verbose,
                    description=annotation.description,
                    html=annotation.html
                ) for annotation in g.annotations.all().order_by('anno_type')]
        ))

    @staticmethod
    def get_tree(request):
        """
        Load phylogenetic tree in Newick tree format.

        Three algorithms are currently supported:
            1) TaxID-based (Simple, almost instantaneous)
            2) ANI-based (Based on whole-genome similarity, reasonably quick)
            3) OrthoFinder-based (Based on single-copy-ortholog alignments, slowest)

        Query:
            - method: 'taxid', 'ani' or 'orthofinder'
            - members[]: list of member identifiers
        """
        if not request.GET:
            return err('did not receive valid JSON')

        if not ('method' in request.GET):
            return err(F"missing parameters. required: 'method'. Got: {request.GET.keys()}")

        method = request.GET.get('method')
        if method not in ['taxid', 'ani', 'orthofinder']:
            return err(F"method must be either taxid', 'ani' or 'orthofinder'. Got: {method}")

        identifiers = set(request.GET.getlist('members[]'))

        if method == 'taxid':
            MODEL = Member
            METHOD = TaxIdTree

        if method == 'ani':
            MODEL = Genome
            METHOD = AniTree

        if method == 'orthofinder':
            MODEL = Genome
            METHOD = OrthofinderTree

        objs = MODEL.objects.filter(identifier__in=identifiers)
        try:
            newick = METHOD(objs).newick
        except TreeNotDoneError as e:
            return JsonResponse(dict(status='still_running', message=e.message), status=409)  # 409 = conflict

        if not len(objs) == len(identifiers):
            found = set(objs.values_list('identifier', flat=True))
            print(F"Could not find these {type(objs.first()).__name__}s: {identifiers.difference(found)}")
            return err(F"Could not find these {type(objs.first()).__name__}s: {identifiers.difference(found)}")

        # create dictionary: strain -> color based on taxid
        species_dict = {o.identifier: o.taxid.taxscientificname for o in objs}

        return JsonResponse(dict(method=method, newick=newick, color_dict=species_dict))
