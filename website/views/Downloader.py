from django.shortcuts import render, HttpResponse
from django.http import JsonResponse

import os
from time import sleep
from website.views.helpers.magic_string import MagicQueryManager
from lib.ogb_cache.ogb_cache import clear_cache
from website.views.helpers.extract_requests import contains_data, extract_data
from website.models import Genome, Organism
from OpenGenomeBrowser.settings import CACHE_DIR, CACHE_MAXSIZE, GENOMIC_DATABASE

# future: use nginx directly
# nginx mod_zip: https://github.com/evanmiller/mod_zip/
# https://github.com/travcunn/django-zip-stream

cache_subdir = 'downloader'

download_abbrs = {
    'organism': 'complete organism',
    'assembly_fasta': 'assembly fasta (fna)',
    'cds_gbk': 'GenBank (gbk)',
    'cds_faa': 'protein fasta (faa)',
    'cds_ffn': 'nucleotide fasta (ffn)',
    'custom_annotations': 'custom files'
}

abbr_to_suffix = {
    'assembly_fasta': 'fna',
    'cds_gbk': 'gbk',
    'cds_faa': 'faa',
    'cds_ffn': 'ffn'
}


def get_cache_path(genomes_hash: str, abbr: str, relative: bool) -> str:
    if relative:
        return os.path.join(cache_subdir, f'{genomes_hash}:{abbr}.tar.gz')
    else:
        return os.path.join(CACHE_DIR, cache_subdir, f'{genomes_hash}:{abbr}.tar.gz')


def is_cached(genomes_hash: str, abbr: str) -> bool:
    return os.path.isfile(get_cache_path(genomes_hash, abbr, relative=False))


def is_changing(genomes_hash: str, abbr: str) -> bool:
    file = get_cache_path(genomes_hash, abbr, relative=False)
    s1 = os.path.getsize(file)
    sleep(0.2)
    s2 = os.path.getsize(file)
    return s1 != s2


def downloader_view(request):
    context = dict(
        title='Downloader',
        error_danger=[], error_warning=[], error_info=[]
    )

    context['genome_to_species'] = '{}'

    if contains_data(request, 'genomes'):
        qs = extract_data(request, 'genomes', list=True)

        try:
            magic_query_manager = MagicQueryManager(queries=qs)
            context['magic_query_manager'] = magic_query_manager

            hash = Genome.hash_genomes(magic_query_manager.all_genomes)

            files_to_download = [
                [verbose, abbr, hash, is_cached(hash, abbr), get_cache_path(hash, abbr, relative=True)]
                for abbr, verbose in download_abbrs.items()
            ]

            print(files_to_download)

            context['files_to_download'] = files_to_download
            context['genomes_hash'] = hash
        except Exception as e:
            context['error_danger'].append(str(e))

    return render(request, 'website/downloader.html', context)


import tarfile


def downloader_submit(request):
    qs = set(request.POST.getlist('genomes[]'))
    hash = request.POST.get('hash', None)
    abbr = request.POST.get('abbr', None)

    try:
        assert abbr in download_abbrs, f'abbr not acceptable. {abbr=} allowed={download_abbrs.keys()}'
        genomes = MagicQueryManager(qs, raise_errors=True).all_genomes
        assert len(genomes) > 0, f'no genomes found'
        assert hash == Genome.hash_genomes(genomes), 'Hash does not match!'
    except Exception as e:
        return JsonResponse(dict(success='false', message=F'magic query is bad: {e}'), status=500)

    print('request download:', abbr, genomes)

    tar_path = get_cache_path(hash, abbr, relative=False)
    os.makedirs(os.path.dirname(tar_path), exist_ok=True)
    try:
        tar = tarfile.open(tar_path, 'w:gz', compresslevel=4)

        # ORGANISM
        if abbr == 'organism':
            organisms = Organism.objects.filter(genome__identifier__in=[g.identifier for g in genomes])
            organisms = organisms.distinct()

            def filterfn(tarinfo):
                return None if os.path.basename(tarinfo.name).startswith('.') else tarinfo

            for o in organisms:
                o: Organism
                tar.add(
                    name=o.base_path(relative=False), arcname=o.name, recursive=True,
                    filter=lambda f: None if os.path.basename(f.name).startswith('.') else f  # ignore hidden files
                )

        # CUSTOM ANNOTATIONS
        elif abbr == 'custom_annotations':
            for g in genomes:
                for cf in getattr(g, abbr):
                    tar.add(name=f'{g.base_path(relative=False)}/{cf["file"]}', arcname=f'{g.identifier}/{cf["file"]}')

        # REQUIRED FILES
        else:
            suffix = abbr_to_suffix[abbr]
            for g in genomes:
                tar.add(name=f'{GENOMIC_DATABASE}/{getattr(g, abbr)(relative=True)}', arcname=f'{g.identifier}.{suffix}')
            print(tar)
    except Exception as e:
        print(e)
        os.remove(tar_path)

    clear_cache(cache_fn_dir=f'{CACHE_DIR}/downloader', maxsize=CACHE_MAXSIZE)

    return JsonResponse(dict(success=True))


def downloader_is_loaded(request):
    hash = request.POST['hash']
    abbr = request.POST['abbr']

    if not is_cached(genomes_hash=hash, abbr=abbr):
        return JsonResponse(dict(is_loaded=False, message='File does not exist (yet).'), status=420)

    if is_changing(genomes_hash=hash, abbr=abbr):
        return JsonResponse(dict(is_loaded=False, message='File is not complete...'), status=420)

    return JsonResponse(dict(is_loaded=True))
