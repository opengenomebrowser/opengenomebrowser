import sys
import os
import json
from progressbar import progressbar  # pip install progressbar2
from colorama import Fore

OGB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(OGB_DIR)

# import django environment to manipulate the Organism and Genome classes
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OpenGenomeBrowser.settings")
from django.core.wsgi import get_wsgi_application
from django.conf import settings

application = get_wsgi_application()

from db_setup.FolderLooper import FolderLooper, MockGenome, MockOrganism

from website.serializers import GenomeSerializer, OrganismSerializer
from website.models import Organism, Genome, Tag, TaxID, GenomeContent, Gene, PathwayMap, Annotation

folder_looper = FolderLooper(settings.GENOMIC_DATABASE)


def print_warning(message, color):
    if bool(True):
        print(color + message)
        print(Fore.WHITE + '', end='')  # set color back to white


def color_print(message: str, color, *args, **kwargs):
    print(color + '', end='')
    print(message, *args, **kwargs)
    print(Fore.WHITE, end='')  # set color back to white


def confirm_delete(color):
    def yes_or_no():
        YesNo = input("Type 'yes' to delete or 'no' to quit the program.")
        YesNo = YesNo.lower()
        if YesNo == "yes":
            return True
        elif YesNo == "no":
            return False
        else:
            return None

    while True:
        print(color + '', end='')
        inp = yes_or_no()
        print(Fore.WHITE, end='')
        if inp is None:
            continue
        elif inp is True:
            print('removing...')
        elif inp is False:
            print("quit program")
            exit(0)
        break


def sanity_check_folder_structure(verbose=True) -> (int, int):
    """
    Run sanity checks on folder structure, including metadata.
    """
    n_organisms = 0
    n_genomes = 0
    for organism in folder_looper.organisms(skip_ignored=True, sanity_check=False):
        if verbose:
            color_print(f'└── Checking {organism.name}', color=Fore.BLUE)
        organism.sanity_check()
        n_organisms += 1
        for genome in organism.genomes(skip_ignored=True, sanity_check=False):
            if verbose:
                color_print(f'   └── Checking {genome.identifier}', color=Fore.GREEN)
            n_genomes += 1
            genome.sanity_check()

    if verbose:
        print(f'\nSanity checks for {n_organisms} organisms and {n_genomes} genomes completed successfully!\n')

    return n_organisms, n_genomes


def import_database(delete_missing: bool = True, auto_delete_missing: bool = False):
    """
    Load organisms and genomes from file database into PostgreSQL database

    :param delete_missing: if True (default), check if organisms/genomes have gone missing
    :param auto_delete_missing: if True, remove missing organisms/genomes without console prompt
    """

    # perform sanity checks
    print('Performing sanity checks...')
    n_organisms, n_genomes = sanity_check_folder_structure(verbose=False)

    # Remove Organism or a Genome if it has been removed from the database-folder
    if delete_missing:
        remove_missing_organisms(auto_delete_missing)

    print(F"Number of organisms to import: {n_organisms}")
    print(F"Number of genomes to import: {n_genomes}")

    organism_generator = folder_looper.organisms(skip_ignored=True, sanity_check=False)
    for organism in progressbar(organism_generator, max_value=n_organisms, redirect_stdout=True):
        organism: MockOrganism
        color_print(f'└── {organism.name}', color=Fore.BLUE, end=' ')

        organism_serializer = OrganismSerializer(data=organism.json)
        organism_serializer.is_valid(raise_exception=True)

        try:
            o = Organism.objects.get(name=organism.name)
            match, difference = OrganismSerializer.json_matches_organism(organism=o, json_dict=organism.json)
            if match:
                print(':: unchanged')

            else:
                print(f':: update: {difference}')
                o = organism_serializer.update(instance=o, validated_data=organism_serializer.validated_data, representative_isnull=True)

        except Organism.DoesNotExist:
            print(':: new')
            o = organism_serializer.create(organism_serializer.validated_data)

        genomes = []

        for genome in organism.genomes(skip_ignored=True, sanity_check=False):
            genome: MockGenome
            color_print(f'   └── {genome.identifier}', color=Fore.GREEN, end=' ')

            genome_serializer = GenomeSerializer(data=genome.json)
            genome_serializer.is_valid(raise_exception=True)

            try:
                g = Genome.objects.get(identifier=genome.identifier)
                match, difference = GenomeSerializer.json_matches_genome(genome=g, json_dict=genome.json, organism_name=o.name)
                if match:
                    print(':: unchanged')

                else:
                    print(f':: update: {difference}')
                    g = genome_serializer.update(instance=g, validated_data=genome_serializer.validated_data, organism=o)

            except Genome.DoesNotExist:
                print(':: new')
                g = genome_serializer.create(genome_serializer.validated_data, organism=o)

            genomes.append(g)

        o.representative = Genome.objects.get(identifier=organism.representative(sanity_check=False).identifier)
        o.save()

        for g in genomes:
            GenomeSerializer.update_genomecontent(g)

    Tag.create_tag_color_css()
    TaxID.create_taxid_color_css()

    sanity_check_postgres()


def reload_color_css():
    Tag.create_tag_color_css()
    TaxID.create_taxid_color_css()


def import_pathway_maps():
    """
    (Re)load pathway maps into PostgreSQL database
    """
    from website.models import PathwayMap
    PathwayMap.reload_maps()


def remove_missing_organisms(auto_delete_missing: bool = False):
    """
    Remove organisms/genomes from the PostgreSQL database if they disappeared from the folder structure

    :param auto_delete_missing: if True, remove missing organisms/genomes without console prompt
    """
    all_organisms = [o.name for o in folder_looper.organisms(skip_ignored=True, sanity_check=False)]
    all_genomes = [g.identifier for g in folder_looper.genomes(skip_ignored=True, sanity_check=False)]

    for genome in Genome.objects.all():
        if genome.identifier not in all_genomes:
            if not auto_delete_missing:
                print_warning(
                    F"Genome '{genome.identifier}' is missing from the database-folder. Remove it from the database?",
                    color=Fore.MAGENTA
                )
                confirm_delete(color=Fore.MAGENTA)
            genome.delete()

    for organism in Organism.objects.all():
        if organism.name not in all_organisms:
            if not auto_delete_missing:
                print_warning(
                    F"Organism '{organism.name}' is missing from the database-folder. Remove it from the database?",
                    color=Fore.MAGENTA
                )
                confirm_delete(color=Fore.MAGENTA)
            organism.delete()


def reset_database(auto_delete: bool = False):
    """
    Removes all objects fromt he PostgreSQL database (Organism, Genome, Tag, TaxID, GenomeContent, Gene, PathwayMap, Annotation)

    :param auto_delete: if True: delete without prompt
    """
    print('Resetting database...')
    if not auto_delete:
        print_warning("DO YOU REALLY WANT TO RESET THE DATABASE?", color=Fore.MAGENTA)
        confirm_delete(color=Fore.MAGENTA)

    for model in [Organism, Genome, Tag, TaxID, GenomeContent, Gene, PathwayMap, Annotation]:
        model.objects.all().delete()


def sanity_check_postgres():
    """
    Perform sanity checks on objects in the database
    """
    print()
    print("Performing sanity checks...")
    # TaxID and Tag check their own invariants upon saving.
    organisms = Organism.objects.all()
    for organism in organisms:
        assert organism.invariant(), F"Class invariant failed for organism '{organism.name}'!"

    genomes = Genome.objects.all()
    for genome in genomes:
        assert genome.invariant(), F"Class invariant failed for genome '{genome.identifier}'!"

    tags = Tag.objects.all()
    for tag in tags:
        assert tag.invariant(), F"Class invariant failed for tag '{tag.tag}'!"

    taxids = TaxID.objects.all()
    for taxid in taxids:
        assert taxid.invariant(), F"Class invariant failed for TaxID '{taxid.id} - {taxid.scientific_name}'!"
    assert Annotation.invariant()

    print(F"Successfully imported: {len(organisms)} organisms and {len(genomes)} genomes, " +
          F"belonging to {len(Organism.objects.values('taxid').distinct())} species.")


def import_orthologs(auto_delete: bool = False):
    """
    Load annotations from settings.py > ORTHOLOG_ANNOTATIONS['ortholog_to_gene_ids']
    """
    if not auto_delete:
        print_warning(
            F"Delete all ortholog annotations?",
            color=Fore.MAGENTA
        )
        confirm_delete(color=Fore.MAGENTA)

    Annotation.load_ortholog_annotations()


def update_bokeh(auto_delete: bool = False):
    """
    """
    import bokeh
    import requests

    bokeh_version = bokeh.__version__
    url_fill = f'-{bokeh_version}'

    if not auto_delete:
        print_warning(
            f'Overwrite bokeh js files? (New version: {bokeh_version})',
            color=Fore.MAGENTA
        )
        confirm_delete(color=Fore.MAGENTA)
        print()

    cdn = 'https://cdn.bokeh.org/bokeh/release'
    js_dir = f'{OGB_DIR}/website/static/global/js'
    files = ['bokeh{}.min.js', 'bokeh-widgets{}.min.js', 'bokeh-tables{}.min.js', 'bokeh-api{}.min.js']

    for file in files:
        url = f'{cdn}/{file.format(url_fill)}'
        target_path = f'{js_dir}/{file.format("")}'
        print(f'{url}  -->>  {target_path}')
        r = requests.get(url, allow_redirects=True)

        with open(target_path, 'wb') as f:
            f.write(r.content)

    print('\nRemember to run "python manage.py collectstatic"!')


def send_mail(to: str):
    from django.core.mail import send_mail

    send_mail(
        subject='Test Mail from OpenGenomeBrowser',
        message='Test Mail Content.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to],
        fail_silently=False,
    )
    print('Mail sent!')


def download_kegg_data(n_parallel=4):
    import requests
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    print('Downloading KEGG data...')

    os.makedirs(settings.ANNOTATION_DATA, exist_ok=True)

    def fetch(session, url, save_path, raw=False):
        with session.get(url) as response:
            if raw:
                data = response.content
                mode = 'wb'
            else:
                data = response.text
                mode = 'w'

            if response.status_code != 200:
                print("FAILURE::{0}".format(url))

            print(F'downloaded {url}')

            with open(save_path, mode) as out:
                out.write(data)

            print(F'wrote {save_path}')

            return data

    async def fetch_all(url_fn_raw_list: list, n_parallel: int):
        with ThreadPoolExecutor(max_workers=n_parallel) as executor:
            with requests.Session() as session:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(
                        executor,
                        fetch,
                        *(session, url, filename, raw)
                    )
                    for url, filename, raw in url_fn_raw_list
                ]
                for response in await asyncio.gather(*tasks):
                    pass

    # files = ['path', 'rn', 'ko', 'compound', 'drug', 'glycan', 'dgroup', 'enzyme']
    files = ['rn', 'ko', 'compound', 'enzyme']
    url_fn_raw_list = [
        (F'http://rest.kegg.jp/list/{file}', F'{settings.ANNOTATION_DATA}/{file}.tsv', False)
        for file in files
    ]

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(fetch_all(url_fn_raw_list=url_fn_raw_list, n_parallel=n_parallel))
    loop.run_until_complete(future)

    if 'enzyme' in files:
        print('Sorting enzyme.tsv')
        # sort enzyme.tsv according to C-language logic
        import subprocess
        myenv = os.environ.copy()
        myenv['LC_ALL'] = 'C'
        subprocess.run(
            F"sort --key=1 --field-separator=$'\t' "
            F"--output={settings.ANNOTATION_DATA}/enzyme_sorted.tsv {settings.ANNOTATION_DATA}/enzyme.tsv",
            shell=True, env=myenv)


if __name__ == "__main__":
    from glacier import glacier

    glacier([
        sanity_check_folder_structure,
        import_database,
        reset_database,
        remove_missing_organisms,
        import_pathway_maps,
        sanity_check_postgres,
        import_orthologs,
        update_bokeh,
        send_mail,
        download_kegg_data,
        reload_color_css
    ])
