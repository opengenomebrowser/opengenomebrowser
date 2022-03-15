import os
from time import sleep
import zipfile
from typing import Callable

from django.shortcuts import render, HttpResponse
from django.http import JsonResponse

from website.views.helpers.extract_errors import extract_errors
from website.views.helpers.magic_string import MagicQueryManager
from lib.ogb_cache.ogb_cache import clear_cache
from website.views.helpers.extract_requests import contains_data, extract_data
from website.models import Genome, Organism
from OpenGenomeBrowser.settings import CACHE_DIR, CACHE_MAXSIZE, FOLDER_STRUCTURE

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
        return os.path.join(cache_subdir, f'{genomes_hash}:{abbr}.zip')
    else:
        return os.path.join(CACHE_DIR, cache_subdir, f'{genomes_hash}:{abbr}.zip')


def is_cached(genomes_hash: str, abbr: str) -> bool:
    return os.path.isfile(get_cache_path(genomes_hash, abbr, relative=False))


def is_changing(genomes_hash: str, abbr: str) -> bool:
    file = get_cache_path(genomes_hash, abbr, relative=False)
    s1 = os.path.getsize(file)
    sleep(0.2)
    s2 = os.path.getsize(file)
    return s1 != s2


def zip_dir(zip_handler: zipfile.ZipFile, name: str, arcname: str, filter: Callable):
    for root, dirs, files in os.walk(name):
        files = [f for f in files if filter(f)]
        dirs[:] = [d for d in dirs if filter(d)]
        for file in files:
            zip_handler.write(
                filename=os.path.join(root, file),
                arcname=os.path.join(arcname, os.path.relpath(os.path.join(root, file), name))
            )


def downloader_view(request):
    context = extract_errors(request, dict(title='Downloader'))

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

            context['files_to_download'] = files_to_download
            context['genomes_hash'] = hash
        except Exception as e:
            context['error_danger'].append(str(e))

    return render(request, 'website/downloader.html', context)


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
        return JsonResponse(dict(success='false', message=f'magic query is bad: {e}'), status=500)

    zip_path = get_cache_path(hash, abbr, relative=False)
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zip:

            # ORGANISM
            if abbr == 'organism':
                organisms = Organism.objects.filter(genome__identifier__in=[g.identifier for g in genomes])
                organisms = organisms.distinct()

                for o in organisms:
                    o: Organism
                    zip_dir(
                        zip_handler=zip,
                        name=o.base_path(relative=False),
                        arcname=o.name,
                        filter=lambda f: not os.path.basename(f).startswith('.')  # ignore hidden files
                    )

            # CUSTOM ANNOTATIONS
            elif abbr == 'custom_annotations':
                for g in genomes:
                    for cf in getattr(g, abbr):
                        zip.write(filename=f'{g.base_path(relative=False)}/{cf["file"]}', arcname=f'{g.identifier}/{cf["file"]}')

            # REQUIRED FILES
            else:
                suffix = abbr_to_suffix[abbr]
                for g in genomes:
                    zip.write(filename=f'{FOLDER_STRUCTURE}/{getattr(g, abbr)(relative=True)}', arcname=f'{g.identifier}.{suffix}')

    except Exception as e:
        print(e)
        os.remove(zip_path)

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
