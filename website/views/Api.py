import json
import itertools
from collections import Counter

from django.shortcuts import HttpResponse
from django.http import JsonResponse
from django.db.models.functions import Concat
from django.db.models import CharField, Value as V

from website.models import GenomeContent, Genome, PathwayMap, Gene, TaxID, GenomeSimilarity, Annotation, annotation_types
from website.models.Tree import TaxIdTree, AniTree, OrthofinderTree, TreeNotDoneError, TreeFailedError

from lib.gene_loci_comparison.gene_loci_comparison import GraphicRecordLocus
from bokeh.embed import components

from lib.multiplesequencealignment.multiple_sequence_alignment import ClustalOmega, MAFFT, Muscle
from website.views.helpers.magic_string import MagicQueryManager, MagicObject


def err(error_message, status=500):
    print(error_message)
    return JsonResponse(dict(success='false', message=error_message), status=status)


UNIQUE_COLORS_HEX = json.load(open('lib/color_generator/300_different_colors.txt'))


class Api:
    @staticmethod
    def autocomplete_pathway(request):
        q = request.GET.get('term')

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
        q = request.GET.get('term')

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
    def autocomplete_genomes(request):
        q = request.GET.get('term')
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
        q = request.GET.get('term')
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
    def annotation_to_type(request):
        annotations = request.POST.getlist('annotations[]')

        annotations = Annotation.objects.filter(name__in=annotations)

        annotation_to_type = {anno.name:
            dict(
                anno_type=anno.anno_type,
                description=anno.description
            )
            for anno in annotations}

        return JsonResponse(annotation_to_type)

    @staticmethod
    def autocomplete_genes(request):
        term = request.GET.get('term', '')
        genome = request.GET.get('genome', None)

        if term is None and genome is None:
            return err('"term" and "genome" are not in request.POST')

        if genome:
            genes = Gene.objects.filter(genomecontent=genome, identifier__icontains=term).order_by('identifier')[:10]
        else:
            genes = Gene.objects.filter(identifier__istartswith=term).order_by('identifier')[:10]

        results = [gene.identifier for gene in genes]

        data = json.dumps(results)
        mimetype = 'application/json'

        return HttpResponse(data, mimetype)

    @staticmethod
    def validate_genomes(request):
        """
        Test if genomes exist in the database.

        Queries may also be "magic words"
        """
        qs = set(request.POST.getlist('genomes[]'))

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
        qs = set(request.POST.getlist('genes[]'))

        found_genes = set(Gene.objects.filter(identifier__in=qs).values_list('identifier', flat=True))
        if not qs == found_genes:
            return JsonResponse(dict(success=False, message='Could not find some identifiers.'))

        return JsonResponse(dict(success=True))

    @staticmethod
    def genome_identifier_to_species(request):
        qs = set(request.POST.getlist('genomes[]'))

        try:
            genome_to_visualization = MagicQueryManager(qs, raise_errors=False).genome_to_visualization()
        except Exception as e:
            return err(f'magic query is bad: {e}')
        return JsonResponse(genome_to_visualization)

    @staticmethod
    def validate_annotations(request):
        """
        Test if annotations exist in the database.
        """
        annotations = set(request.POST.getlist('annotations[]'))

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
        success = PathwayMap.objects.filter(slug=request.POST['slug']).exists()

        return JsonResponse(dict(success=success))

    @staticmethod
    def dna_feature_viewer_single(request):
        """
        Get dna_feature_viewer bokeh around gene_identifier.

        Query: gene_identifier = "organism3_000345", span=10000

        Returns bokeh script and div
        """
        span = int(request.POST['span'])

        gene_identifier = request.POST.get('gene_identifier')

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
    def dna_feature_viewer_multi(request):
        """
        Get dna_feature_viewer bokeh around gene_identifier.

        Query: gene_identifiers = ["organism3_000345", "organism2_000445"], span=10000

        Returns bokeh script and div
        """
        span = int(request.POST['span'])

        colorize_by = request.POST['colorize_by']
        allowed_colorize_bys = list(annotation_types.keys()) + ['--']
        if colorize_by not in allowed_colorize_bys:
            return err(F"colorize_by must be one of the following: {allowed_colorize_bys}, but is {colorize_by}")

        gene_identifiers = request.POST.getlist('gene_identifiers[]')

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
            plot_div += f'''
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
        gene_identifiers = request.POST.getlist('gene_identifiers[]')
        method = request.POST['method']
        sequence_type = request.POST['sequence_type']

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

        alignment = METHOD.align(fastas=FASTAS, seq_type=sequence_type)

        return JsonResponse(dict(fastas=FASTAS, method=method, version=version, alignment=alignment))

    @staticmethod
    def get_gene(request):
        """
        Get information about a gene.

        Query: gene_identifier = "organism3_000345"

        Returns JSON
        """
        gene_identifier = request.POST.get('gene_identifier')

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
        method = request.POST.get('method')

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

        identifiers = set(request.POST.getlist('genomes[]'))
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
            return JsonResponse(dict(status='still_running', message=e.message), status=420)  # 420 = enhance your calm (but nginx changes 408!)
        except TreeFailedError as e:
            return JsonResponse(dict(status='still_running', message=e.message), status=500)  # 500 = internal server error

        if hasattr(tree, 'distance_matrix'):
            result['distance-matrix'] = tree.distance_matrix.to_csv()

        if hasattr(tree, 'cache_file_path'):
            result['cache-file-path'] = tree.cache_file_path
            result['has-cache-file'] = tree.has_cache_file

        return JsonResponse(result)

    @staticmethod
    def reload_orthofinder(request):
        """
        Trigger recalculation of OrthoFinder for specific genomes. This reloads the cache.

        Query:
            - genomes[]: list of genome identifiers
        """
        identifiers = set(request.POST.getlist('genomes[]'))
        genomes = Genome.objects.filter(identifier__in=identifiers)
        if not len(genomes) == len(identifiers):
            found = set(genomes.values_list('identifier', flat=True))
            print(F"Could not find these {type(genomes.first()).__name__}s: {identifiers.difference(found)}")
            return err(F"Could not find these {type(genomes.first()).__name__}s: {identifiers.difference(found)}")

        from website.models import CoreGenomeDendrogram
        hash = Genome.hash_genomes(genomes=genomes)
        cgd = CoreGenomeDendrogram.objects.get(unique_id=hash)
        if cgd.status != 'R' or 'force' in request.POST:
            cgd.reload()
            return JsonResponse(dict(success=True, message='triggered recalculation successfully'))
        else:
            return JsonResponse(dict(success=False, message='already running'))
