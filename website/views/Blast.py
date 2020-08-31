from django.shortcuts import render, HttpResponse
from website.views.helpers.magic_string import MagicString
from django.http import HttpResponseBadRequest
from lib.ncbiblast.ncbi_blast.blast_wrapper import Blast

blast = Blast(system_blast=False, outfmt=5)

choice_to_settings = dict(
    blastn_ffn=dict(query_type='nucl', db_type='nucl', file_type='blast_db_ffn'),
    blastn_fna=dict(query_type='nucl', db_type='nucl', file_type='blast_db_fna'),
    blastp=dict(query_type='prot', db_type='prot', file_type='blast_db_faa'),
    blastx=dict(query_type='nucl', db_type='prot', file_type='blast_db_faa'),
    tblastn_ffn=dict(query_type='prot', db_type='nucl', file_type='blast_db_ffn'),
    tblastn_fna=dict(query_type='prot', db_type='nucl', file_type='blast_db_fna')
)


def blast_view(request):
    context = dict(title='Blast')

    context['genome_to_species'] = '{}'

    if 'genomes' in request.GET:
        qs = set(request.GET['genomes'].split(' '))

        try:
            found_genomes = MagicString.get_genomes(queries=qs)
            context['genomes'] = found_genomes
            context['genome_to_species'] = {genome.identifier: genome.taxscientificname for genome in found_genomes}
        except ValueError as e:
            context['error_danger'] = str(e)

    print('come here')

    return render(request, 'website/blast.html', context)


def blast_submit(request):
    print('blast-submit')
    if not request.method == 'POST':
        return HttpResponseBadRequest('Only POST requests allowed.')

    for i in ['blast_input', 'blast_type', 'genomes[]']:
        if not i in request.POST:
            return HttpResponse('Request failed: does not include. ' + i)

    try:
        genomes = MagicString.get_genomes(request.POST['genomes[]'].split(' '))
    except ValueError as e:
        return HttpResponse('Request failed: genomes[] incorrect. ' + str(e))

    query = request.POST['blast_input']
    blast_type = request.POST['blast_type']
    query_type = choice_to_settings[blast_type]['query_type']
    db_type = choice_to_settings[blast_type]['db_type']
    blast_algorithm = request.POST['blast_type'].split('_')[0]

    file_type = choice_to_settings[blast_type]['file_type']

    fasta_files = [getattr(genome.genomecontent, file_type)(relative=False) for genome in genomes]

    blast_output = blast.blast(fasta_string=query, db=fasta_files, mode=blast_algorithm)

    return HttpResponse(blast_output, content_type="text/plain")
