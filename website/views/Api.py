from django.shortcuts import HttpResponse
from django.http import JsonResponse
import json
import itertools
from collections import Counter

from OpenGenomeBrowser import settings
from website.models import GenomeContent, Genome, PathwayMap, Gene, TaxID, GenomeSimilarity, Annotation, annotation_types
from website.models.Tree import TaxIdTree, AniTree, OrthofinderTree, TreeNotDoneError
from django.db.models.functions import Concat
from django.db.models import CharField, Value as V

from lib.gene_loci_comparison.gene_loci_comparison import GraphicRecordLocus
from bokeh.embed import components

from lib.multiplesequencealignment.multiple_sequence_alignment import ClustalOmega, MAFFT, Muscle
from .helpers.magic_string import MagicQueryManager, MagicObject


def err(error_message, status=500):
    print(error_message)
    return JsonResponse(dict(status='false', message=error_message), status=status)


UNIQUE_COLORS_HEX = json.load(open('lib/tax_id_to_color/300_different_colors.txt'))


class Api:
    @staticmethod
    def annotation_to_type(request):
        if not request.GET:
            return err('did not receive valid JSON')

        if not ('annotations[]' in request.GET):
            return err(F"missing parameter 'annotations[]'. Got: {request.GET.keys()}")

        annotations = request.GET.getlist('annotations[]')

        annotations = Annotation.objects.filter(name__in=annotations)

        annotation_to_type = {anno.name:
            dict(
                anno_type=anno.anno_type,
                description=anno.description
            )
            for anno in annotations}

        return JsonResponse(annotation_to_type)

    @staticmethod
    def autocomplete_pathway(request):
        if not 'term' in request.GET:
            return err('"term" not in request.GET')

        q = request.GET.get('term', '')

        # create 'synthetic' charfield
        # https://docs.djangoproject.com/en/2.2/ref/models/database-functions/#concat
        all_maps = PathwayMap.objects.annotate(slug_and_title=Concat(
            'slug', V(' : '), 'title',
            output_field=CharField()
        )).all()

        maps = all_maps.filter(slug_and_title__icontains=q)[:20]  # return 20 results
        results = []
        for map in maps:
            results.append({
                'label': map.slug_and_title,
                'value': map.slug_and_title
            })
        data = json.dumps(results)
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)

    @staticmethod
    def autocomplete_annotations(request):
        if not 'term' in request.GET:
            return err('"term" not in request.GET')

        q = request.GET.get('term', '')

        try:
            annotations = Annotation.objects.filter(name__istartswith=q)[:20]
        except Annotation.DoesNotExist:
            annotations = []

        results = []
        for annotation in annotations:
            results.append({
                'label': F"{annotation.name} ({annotation.description})",
                'value': annotation.name
            })
        data = json.dumps(results)
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)

    @staticmethod
    def search_genes(request):
        term = request.GET.get('term', None)

        genome = request.GET.get('genome', None)

        if term is None and genome is None:
            return err('"term" and "genome" are not in request.GET')

        if genome:
            genes = Gene.objects.filter(genomecontent=genome, identifier__icontains=term if term else '').order_by('identifier')[:10]
        else:
            genes = Gene.objects.filter(identifier__istartswith=term).order_by('identifier')[:10]

        results = [gene.identifier for gene in genes]

        data = json.dumps(results)
        mimetype = 'application/json'

        return HttpResponse(data, mimetype)

    @staticmethod
    def autocomplete_genomes(request):
        if not 'term' in request.GET:
            return err('"term" not in request.GET')

        q = request.GET.get('term', '')
        results = []

        if q.startswith('@'):
            results.extend(MagicObject.autocomplete(magic_string=q))
        else:
            genomes = GenomeContent.objects.filter(identifier__icontains=q)[:20]
            genomes.prefetch_related('organism__taxid')
            for genome in genomes:
                results.append({
                    'label': F"{genome.identifier} ({genome.organism.taxid.taxscientificname})",
                    'value': genome.identifier
                })

        data = json.dumps(results)
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)

    @staticmethod
    def autocomplete_genes(request):
        if not 'term' in request.GET:
            return err('"term" not in request.GET')

        q = request.GET.get('term', '')
        results = []

        genes = Gene.objects.filter(identifier__icontains=q)[:20]
        genes.prefetch_related('genomecontent__genome__organism__taxid')
        for gene in genes:
            results.append({
                'label': F"{gene.identifier} ({gene.genomecontent.genome.organism.taxid.taxscientificname})",
                'value': gene.identifier
            })

        data = json.dumps(results)
        mimetype = 'application/json'
        return HttpResponse(data, mimetype)

    @staticmethod
    def validate_genomes(request):
        """
        Test if genomes exist in the database.

        Queries may also be "magic words"
        """
        if not request.GET:
            return err('did not receive valid JSON')

        if not 'genomes[]' in request.GET:
            return err('did not receive genomes[]')

        qs = set(request.GET.getlist('genomes[]'))

        try:
            MagicQueryManager(queries=qs)
        except Exception as e:
            return JsonResponse(dict(success=False, message=str(e)))

        return JsonResponse(dict(success=True))

    @staticmethod
    def validate_genes(request):
        """
        Test if genomes exist in the database.

        Queries may also be "magic words"
        """
        if not request.GET:
            return err('did not receive valid JSON')

        if not 'genes[]' in request.GET:
            return err('did not receive genes[]')

        qs = set(request.GET.getlist('genes[]'))

        found_genes = set(Gene.objects.filter(identifier__in=qs).values_list('identifier', flat=True))
        if not qs == found_genes:
            return JsonResponse(dict(success=False, message='Could not find some identifiers.'))

        return JsonResponse(dict(success=True))

    @staticmethod
    def genome_identifier_to_species(request):
        if not request.GET:
            return err('did not receive valid JSON')

        if not ('genomes[]' in request.GET):
            return err(F"missing parameter 'genomes[]'. Got: {request.GET.keys()}")

        qs = set(request.GET.getlist('genomes[]'))

        try:
            genome_to_species = MagicQueryManager(qs, raise_errors=False).genome_to_species()
        except Exception as e:
            return err(F'magic query is bad: {e}')
        return JsonResponse(genome_to_species)

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
    def validate_pathwaymap(request):
        """
        Test if map_id exist in the database.
        """
        if not request.GET:
            return err('did not receive valid JSON')

        if not 'slug' in request.GET:
            return err('did not receive slug')

        success = PathwayMap.objects.filter(slug=request.GET['slug']).exists()

        return JsonResponse(dict(success=success))

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

        found_annotations = Annotation.objects.filter(name__in=annotations)

        anno_to_description = {anno.name: anno.description for anno in found_annotations}

        return JsonResponse(anno_to_description)

    @staticmethod
    def dna_feature_viewer_single(request):
        """
        Get dna_feature_viewer bokeh around gene_identifier.

        Query: gene_identifier = "organism3_000345", span=10000

        Returns bokeh script and div

        Todo: Ability to change span around gene_locus
        """

        if not request.GET:
            return err('did not receive valid JSON')

        if not ('gene_identifier' in request.GET):
            return err(F"missing parameters. required: 'gene_identifier'. Got: {request.GET.keys()}")

        if not ('span' in request.GET):
            return err(F"missing parameters. required: 'span'. Got: {request.GET.keys()}")

        span = int(request.GET['span'])

        gene_identifier = request.GET.get('gene_identifier')

        g = Gene.objects.get(identifier=gene_identifier)

        graphic_record = GraphicRecordLocus(
            gbk_file=g.genomecontent.genome.cds_gbk(relative=False),
            locus_tag=gene_identifier,
            span=span
        )

        graphic_record.colorize_graphic_record({gene_identifier: '#1984ff'}, strict=False, default_color='#ffffff')

        plot = graphic_record.plot_with_bokeh(
            figure_width=11.4,  # width of .container divs
            figure_height='auto',
            viewspan=3000
        )

        script, plot_div = components(plot)
        script = script[33:-10]  # remove <script type="text/javascript"> and </script>

        return JsonResponse(dict(script=script, plot_div=plot_div))

    @staticmethod
    def align(request):
        """
        Align genes. (Multiple Sequence Alignment)

        Three algorithms are currently supported:
            1) Clustal Omega (clustalo)
            2) MAFFT (mafft)
            3) Muscle (muscle)

        Query:
            - gene_identifiers[]: list of gene identifiers
            - method = 'clustalo', mafft, muscle'
            - sequence_type: 'dna', 'protein'
        """

        if not request.GET:
            return err('did not receive valid JSON')

        if not ('gene_identifiers[]' in request.GET):
            return err(F"missing parameters. required: 'gene_identifiers[]'. Got: {request.GET.keys()}")

        if not ('method' in request.GET):
            return err(F"missing parameters. required: 'method'. Got: {request.GET.keys()}")

        if not ('sequence_type' in request.GET):
            return err(F"missing parameters. required: 'sequence_type'. Got: {request.GET.keys()}")

        print(request.GET)

        gene_identifiers = request.GET.getlist('gene_identifiers[]')
        print(gene_identifiers)
        method = request.GET['method']
        sequence_type = request.GET['sequence_type']

        print(gene_identifiers, method, sequence_type)

        genes = Gene.objects.filter(identifier__in=gene_identifiers)
        if not len(set(gene_identifiers)) == len(genes):
            return err(F"{len(set(gene_identifiers))} were submitted but only {len(genes)} genes were found.")

        if sequence_type == 'dna':
            FASTAS = [g.fasta_nucleotide() for g in genes]
        elif sequence_type == 'protein':
            try:
                FASTAS = [g.fasta_protein() for g in genes]
            except KeyError as e:
                return err(str(e))
        else:
            return err(F"'sequence_type' must be either 'dna' or 'protein', got {sequence_type}.")

        if method == 'clustalo':
            METHOD = ClustalOmega()
        elif method == 'mafft':
            METHOD = MAFFT()
        elif method == 'muscle':
            METHOD = Muscle()
        else:
            return err(F"'method' must be either 'clustalo', 'mafft' or 'muscle', got {method}.")

        version = METHOD.version()

        print(version)
        print(FASTAS)
        alignment = METHOD.align(fastas=FASTAS, seq_type=sequence_type)

        return JsonResponse(dict(fastas=FASTAS, method=method, version=version, alignment=alignment))

    @staticmethod
    def dna_feature_viewer_multi(request):
        """
        Get dna_feature_viewer bokeh around gene_identifier.

        Query: gene_identifiers = ["organism3_000345", "organism2_000445"], span=10000

        Returns bokeh script and div
        """

        if not request.GET:
            return err('did not receive valid JSON')

        if not ('gene_identifiers[]' in request.GET):
            return err(F"missing parameters. required: 'gene_identifiers[]'. Got: {request.GET.keys()}")

        if not ('span' in request.GET):
            return err(F"missing parameters. required: 'span'. Got: {request.GET.keys()}")

        if not ('colorize_by' in request.GET):
            return err(F"missing parameters. required: 'colorize_by'. Got: {request.GET.keys()}")

        span = int(request.GET['span'])

        colorize_by = request.GET['colorize_by']
        allowed_colorize_bys = list(annotation_types.keys()) + ['--']
        if colorize_by not in allowed_colorize_bys:
            return err(F"colorize_by must be one of the following: {allowed_colorize_bys}, but is {colorize_by}")

        gene_identifiers = request.GET.getlist('gene_identifiers[]')

        gs = Gene.objects.filter(identifier__in=gene_identifiers)

        loci_of_interest = [
            dict(gbk=g.genomecontent.genome.cds_gbk(relative=False), gene=g.identifier, title=g.identifier)
            for g in gs]

        graphic_records = GraphicRecordLocus.get_multiple(
            loci_of_interest,
            locus_to_color_dict={},
            span=span
        )

        locus_tags = set()
        for graphic_record in graphic_records:
            locus_tags = locus_tags.union(graphic_record.get_locus_tags())

        genes = Gene.objects.filter(identifier__in=locus_tags)

        def get_ortholog(gene):
            o = gene.annotations.filter(anno_type=colorize_by).first()
            if o is not None:
                return o.name

        locus_tag_to_ortholog = {gene.identifier: get_ortholog(gene) for gene in genes}
        # only color orthologs that occur more than once
        orthologs = [ortholog for ortholog, counts in Counter(locus_tag_to_ortholog.values()).items() if counts > 1]
        # assign random colors to orthologs
        orthologs_to_color = {o: c for o, c in zip(orthologs, itertools.cycle(UNIQUE_COLORS_HEX))}

        locus_tag_to_color = {identifier: orthologs_to_color[ortholog]
                              for identifier, ortholog in locus_tag_to_ortholog.items()
                              if ortholog in orthologs_to_color and ortholog is not None}

        # color selected genes in blue:
        for gbk, id, id_ in loci_of_interest:
            locus_tag_to_color[id] = '#1984ff'

        for graphic_record in graphic_records:
            graphic_record.colorize_graphic_record(locus_tag_to_color)

        plots = GraphicRecordLocus.plot_multiple_bokeh(graphic_records, viewspan=3000, auto_reverse=True)

        script, plot_divs = components(plots)
        script = script[33:-10]  # remove <script type="text/javascript"> and </script>

        gene_divs = [g.html for g in gs]
        species_divs = [g.genomecontent.organism.taxid.html for g in gs]

        plot_div = ""
        for gene, species, plot in zip(gene_divs, species_divs, plot_divs):
            plot_div += F'''
<div class='locus-plot'>
    <div class='locus-plot-header'>
        <div class='handle-div'>
            <i class='handle'>&nbsp&nbsp&nbsp&nbsp</i>
        </div>
        {species} {gene}
    </div>
    {plot}
</div>
'''

        return JsonResponse(dict(script=script, plot_div=plot_div))

    @staticmethod
    def get_gene(request):
        """
        Get information about a gene.

        Query: gene_identifier = "organism3_000345"

        Returns JSON
        """

        if not request.GET:
            return err('did not receive valid JSON')

        if not ('gene_identifier' in request.GET):
            return err(F"missing parameters. required: 'gene_identifier'. Got: {request.GET.keys()}")

        gene_identifier = request.GET.get('gene_identifier')

        g = Gene.objects.get(identifier=gene_identifier)

        def jsonify_annotation(a: Annotation):
            return dict(
                name=a.name,
                anno_type=a.anno_type,
                anno_type_verbose=a.anno_type_verbose,
                description=a.description,
                html=a.html
            )

        annotype_to_gene = {}
        for annotation in g.annotations.all():
            if annotation.anno_type not in annotype_to_gene:
                annotype_to_gene[annotation.anno_type] = [jsonify_annotation(annotation)]
            else:
                annotype_to_gene[(annotation.anno_type)].append(jsonify_annotation(annotation))

        return JsonResponse(dict(
            genome=g.genomecontent.identifier,
            genome_html=g.genomecontent.genome.html,
            species=g.genomecontent.taxid.taxscientificname,
            taxid=g.genomecontent.taxid.id,
            identifier=g.identifier,
            annotype_to_gene=annotype_to_gene,
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
            - method: 'taxid', 'genome-similarity' or 'orthofinder'
            - genomes[]: list of genome identifiers
        """
        if not request.GET:
            return err('did not receive valid JSON')

        if not ('method' in request.GET):
            return err(F"missing parameters. required: 'method'. Got: {request.GET.keys()}")

        method = request.GET.get('method')

        if method == 'taxid':
            MODEL = Genome
            METHOD = TaxIdTree

        elif method == 'genome-similarity':
            MODEL = GenomeContent
            METHOD = AniTree

        elif method == 'orthofinder':
            MODEL = GenomeContent
            METHOD = OrthofinderTree

        else:
            return err(F"method must be either taxid', 'genome-similarity' or 'orthofinder'. Got: {method}")

        identifiers = set(request.GET.getlist('genomes[]'))

        objs = MODEL.objects.filter(identifier__in=identifiers)

        if not len(objs) == len(identifiers):
            found = set(objs.values_list('identifier', flat=True))
            print(F"Could not find these {type(objs.first()).__name__}s: {identifiers.difference(found)}")
            return err(F"Could not find these {type(objs.first()).__name__}s: {identifiers.difference(found)}")

        # create dictionary: organism -> color based on taxid
        species_dict = {o.identifier: o.taxid.taxscientificname for o in objs}

        try:
            tree = METHOD(objs)
            result = dict(method=method, newick=tree.newick, color_dict=species_dict)
        except TreeNotDoneError as e:
            return JsonResponse(dict(status='still_running', message=e.message), status=409)  # 409 = conflict

        if hasattr(tree, 'distance_matrix'):
            result['distance-matrix'] = tree.distance_matrix.to_csv()

        return JsonResponse(result)
