from django.shortcuts import render, HttpResponse

from website.views.helpers.extract_errors import extract_errors
from website.views.helpers.magic_string import MagicQueryManager, MagicError
from django.http import HttpResponseBadRequest
from website.views.helpers.extract_requests import contains_data, extract_data
from plugins import calculate_blast

choice_to_settings = dict(
    blastn_ffn=dict(
        query_type='nucl', db_type='nucl', file_type='blast_db_ffn'
    ),
    blastn_fna=dict(
        query_type='nucl', db_type='nucl', file_type='blast_db_fna'
    ),
    blastp=dict(
        query_type='prot', db_type='prot', file_type='blast_db_faa'
    ),
    blastx=dict(
        query_type='nucl', db_type='prot', file_type='blast_db_faa'
    ),
    tblastn_ffn=dict(
        query_type='prot', db_type='nucl', file_type='blast_db_ffn'
    ),
    tblastn_fna=dict(
        query_type='prot', db_type='nucl', file_type='blast_db_fna'
    )
)


def blast_view(request):
    context = extract_errors(request, dict(title='Blast'))

    context['genome_to_species'] = '{}'

    if contains_data(request, 'genomes'):
        qs = extract_data(request, 'genomes', list=True)

        try:
            magic_query_manager = MagicQueryManager(queries=qs)
            context['magic_query_manager'] = magic_query_manager
        except (ValueError, MagicError) as e:
            context['error_danger'].append(str(e))

    return render(request, 'website/blast.html', context)


def blast_submit(request):
    if not request.method == 'POST':
        return HttpResponseBadRequest('Only POST requests allowed.')

    for i in ['blast_input', 'blast_type', 'genomes[]']:
        if not i in request.POST:
            return HttpResponse('Request failed: does not include. ' + i)

    try:
        magic_query_manager = MagicQueryManager(queries=request.POST['genomes[]'].split(' '))
        genomes = magic_query_manager.all_genomes
    except Exception as e:
        return HttpResponse('Request failed: genomes[] incorrect. ' + str(e))

    query = request.POST['blast_input']
    blast_type = request.POST['blast_type']
    query_type = choice_to_settings[blast_type]['query_type']
    db_type = choice_to_settings[blast_type]['db_type']
    blast_algorithm = request.POST['blast_type'].split('_')[0]

    file_type = choice_to_settings[blast_type]['file_type']

    fasta_files = [getattr(genome.genomecontent, file_type)(relative=True) for genome in genomes]

    # make hashable for caching
    fasta_files = tuple(sorted(set(fasta_files)))

    try:
        blast_output = calculate_blast(fasta_string=query, db=fasta_files, mode=blast_algorithm)
    except Exception as e:
        print(e)
        return HttpResponse('Blast failed. Reason:' + str(e))

    return HttpResponse(blast_output, content_type="text/plain")
