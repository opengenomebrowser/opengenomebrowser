import sys
import os
import json
from progressbar import progressbar
from colorama import Fore
from django.db import transaction

if __name__ == "__main__":
    # import django environment to manipulate the Organism and Genome classes
    OGB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(OGB_DIR)
    import OpenGenomeBrowser.wsgi

from OpenGenomeBrowser import settings

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
        try:
            is_identical, differences = OrganismSerializer().json_matches_organism(
                organism=Organism.objects.get(name=organism.name),
                json_dict=organism.json
            )
            if not is_identical:
                print(f'Difference between organism.json and postgres: {differences}')
        except:
            pass
        n_organisms += 1

        for genome in organism.genomes(skip_ignored=True, sanity_check=False):
            if verbose:
                color_print(f'   └── Checking {genome.identifier}', color=Fore.GREEN)
            n_genomes += 1
            genome.sanity_check()
            try:
                is_identical, differences = GenomeSerializer().json_matches_genome(
                    genome=Genome.objects.get(identifier=genome.identifier),
                    json_dict=genome.json,
                    organism_name=organism.name
                )
                if not is_identical:
                    print(f'Difference between genome.json and postgres: {differences}')
            except:
                pass
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
        import_organism(organism.name, update_css=False)

    reload_color_css()
    sanity_check_postgres()


def reload_organism_genomecontents(name: str = None, all: bool = False, assembly_stats_only: bool = False):
    """
    Forcefully reload fastas and annotations into database.

    :param name: name of an organism
    :param all: if True, process all organisms
    """
    if name:
        with transaction.atomic():
            organism = Organism.objects.get(name=name)
            for genome in organism.genome_set.all():
                if assembly_stats_only:
                    genome.update_assembly_info()
                else:
                    GenomeSerializer.update_genomecontent(genome, wipe=True)
    elif all:
        for organism in progressbar(Organism.objects.all(), max_value=Organism.objects.count(), redirect_stdout=True):
            print(f'└── {organism.name}')
            with transaction.atomic():
                for genome in organism.genome_set.all():
                    print(f'   └── {genome.identifier}')
                    if assembly_stats_only:
                        genome.update_assembly_info()
                    else:
                        GenomeSerializer.update_genomecontent(genome, wipe=True)
    else:
        raise AssertionError('Do nothing. Please specify --name=<organism-name> or --all')

    if not assembly_stats_only:
        print('consider reloading orthologs.')


def import_organism(name: str, update_css: bool = True):
    """
    Import organism into database
    """
    organism = MockOrganism(path=f'{settings.GENOMIC_DATABASE}/organisms/{name}')
    with transaction.atomic():
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

    if update_css:
        reload_color_css()
        sanity_check_postgres()
        print('consider reloading orthologs.')


def remove_organism(name: str):
    """
    Remove organism from database
    """
    Organism.objects.get(name=name).delete()
    GenomeContent.objects.filter(genome__isnull=True).delete()


def reload_color_css() -> None:
    """
    Recreate Tag and TaxID css files:
        /static/global/css/tag_color.css
        /static/global/css/taxid_color.css
    """
    Tag.create_tag_color_css()
    TaxID.create_taxid_color_css()
    Annotation.create_annotype_color_css()


def import_pathway_maps() -> None:
    """
    (Re)load pathway maps into PostgreSQL database
    """
    from website.models import PathwayMap
    PathwayMap.reload_maps()


def remove_missing_organisms(auto_delete_missing: bool = False) -> None:
    """
    Remove organisms/genomes from the PostgreSQL database if they disappeared from the folder structure

    :param auto_delete_missing: if True, remove missing organisms/genomes without console prompt
    """
    all_organisms = [o.name for o in folder_looper.organisms(skip_ignored=True, sanity_check=False)]
    all_genomes = [g.identifier for g in folder_looper.genomes(skip_ignored=True, sanity_check=False)]

    for organism in Organism.objects.all():
        if organism.name not in all_organisms:
            if not auto_delete_missing:
                print_warning(
                    F"Organism '{organism.name}' is missing from the database-folder. Remove it from the database?",
                    color=Fore.MAGENTA
                )
                confirm_delete(color=Fore.MAGENTA)
            organism.delete()

    for genome in Genome.objects.all():
        if genome.identifier not in all_genomes:
            if not auto_delete_missing:
                print_warning(
                    F"Genome '{genome.identifier}' is missing from the database-folder. Remove it from the database?",
                    color=Fore.MAGENTA
                )
                confirm_delete(color=Fore.MAGENTA)
            genome.delete()

    GenomeContent.objects.filter(genome__isnull=True).delete()


def reset_database(auto_delete: bool = False) -> None:
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


def sanity_check_postgres() -> None:
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


def import_orthologs(auto_delete: bool = False) -> None:
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


def backup_genome_similarities(file: str):
    from website.models.GenomeSimilarity import GenomeSimilarity
    done_objects = GenomeSimilarity.objects.filter(status='D')
    assert not os.path.isfile(file), f'file {file} already exists!'
    with open(file, 'w') as f:
        for from_genome, to_genome, similarity in done_objects.values_list('from_genome', 'to_genome', 'similarity'):
            f.write(f'{from_genome}\t{to_genome}\t{similarity}\n')


def import_genome_similarities(file: str, ignore_conflicts: bool = False):
    from website.models.GenomeSimilarity import GenomeSimilarity

    identifier_to_genome = {g.identifier: g for g in GenomeContent.objects.all()}

    def line_to_object(line) -> GenomeSimilarity:
        from_genome, to_genome, similarity = line.split()
        return GenomeSimilarity(
            from_genome=identifier_to_genome[from_genome],
            to_genome=identifier_to_genome[to_genome],
            similarity=float(similarity),
            status='D'
        )

    with open(file) as f:
        objects = [line_to_object(line) for line in f]

    GenomeSimilarity.objects.bulk_create(objects, ignore_conflicts=ignore_conflicts)


def update_bokeh(auto_delete: bool = False) -> None:
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


def send_mail(to: str) -> None:
    """
    Send test mail via DJANGO

    :param to: email address of recipient
    """
    from django.core.mail import send_mail

    try:
        send_mail(
            subject='Test Mail from OpenGenomeBrowser',
            message='Test Mail Content.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to],
            fail_silently=False,
        )
    except Exception as e:
        print(f'mail settings:\n', {
            'EMAIL_HOST': settings.EMAIL_HOST,
            'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
            'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
            'EMAIL_PORT': settings.EMAIL_PORT
        })
        raise e

    print('Mail sent!')


def download_go_data() -> None:
    from lib.gene_ontology.gene_ontology import GeneOntology

    GeneOntology(reload=True)


def download_kegg_data(n_parallel=4) -> None:
    import requests
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    print('Downloading KEGG data...')

    os.makedirs(settings.ANNOTATION_DESCRIPTIONS, exist_ok=True)

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

            print(f'downloaded {url}')

            with open(save_path, mode) as out:
                out.write(data)

            print(f'wrote {save_path}')

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
    files = [('rn', 'KR.tsv'), ('ko', 'KG.tsv'), ('compound', 'CP.tsv'), ('enzyme', 'EC-unsorted.tsv')]
    url_fn_raw_list = [
        (f'http://rest.kegg.jp/list/{type}', f'{settings.ANNOTATION_DESCRIPTIONS}/{filename}', False)
        for type, filename in files
    ]

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(fetch_all(url_fn_raw_list=url_fn_raw_list, n_parallel=n_parallel))
    loop.run_until_complete(future)

    print('Sorting EC.tsv')
    # sort EC-unsorted.tsv according to C-language logic
    import subprocess
    myenv = os.environ.copy()
    myenv['LC_ALL'] = 'C'
    subprocess.run(
        F"sort --key=1 --field-separator=$'\t' "
        F"--output={settings.ANNOTATION_DESCRIPTIONS}/EC.tsv {settings.ANNOTATION_DESCRIPTIONS}/EC-unsorted.tsv",
        shell=True, env=myenv)
    os.remove(f'{settings.ANNOTATION_DESCRIPTIONS}/EC-unsorted.tsv')


def load_annotation_descriptions(anno_type: str = None, reload: bool = True) -> None:
    """
    Reload annotation-description files.

    :param anno_type: e.g. 'EC', 'GC', 'GO', 'GP', 'KG', 'KR' or 'OL'
    :param reload: if True: reload all description, else: only load where no description exists yet
    """
    if anno_type is None:
        anno_types = None
    else:
        anno_types = [anno_type]

    Annotation.load_descriptions(anno_types=anno_types, reload=reload)


def load_blast_dbs(reload=False) -> None:
    """
    Create missing blast_dbs.

    :param reload: if True: Recreate all blast_dbs. (This may be useful when NCBI changes their blast db version.)
    """

    def blast_dbs_exist(gc: GenomeContent) -> bool:
        for f in [gc.blast_db_fna(relative=False), gc.blast_db_faa(relative=False), gc.blast_db_ffn(relative=False)]:
            if not os.path.isfile(f):
                return False
        return True

    gcs = GenomeContent.objects.all()
    n_gcs = len(gcs)
    for i, gc in enumerate(gcs):
        if reload or not blast_dbs_exist(gc):
            print(f'Creating blast-db {i + 1}/{n_gcs}: {gc.identifier}')
            gc.create_blast_dbs(reload=True)


@transaction.atomic
def update_taxids(download_taxdump: bool = False) -> None:
    """
    Update OpenGenomeBrowser TaxIDs to NCBI taxdump.

    :param download_taxdump: if true, download newest taxdump
    """

    if download_taxdump:
        from lib.get_tax_info.get_tax_info import GetTaxInfo
        GetTaxInfo().update_ncbi_taxonomy_from_web()

    with transaction.atomic():
        organisms = Organism.objects.all()

        print('sanity check: metadata taxid must be same as db taxid')
        for o in organisms:
            metadata_taxid = json.load(open(o.metadata_json))['taxid']
            db_taxid = o.taxid.id
            assert metadata_taxid == db_taxid, f'{o} has inconsistent taxid metadata: in db: {db_taxid}, in json: {metadata_taxid}'

        print('set taxid to taxid 1 (root)')
        root_taxid = TaxID.objects.get(id=1)
        organisms.update(taxid=root_taxid)

        print('remove all other taxids')
        TaxID.objects.exclude(id=1).delete()

        print('recreate taxids')
        for o in organisms:
            metadata_taxid = json.load(open(o.metadata_json))['taxid']
            o.taxid = TaxID.get_or_create(taxid=metadata_taxid)

        print('update organisms')
        Organism.objects.bulk_update(organisms, ['taxid'])
        print('done')


def postgres_vacuum(full: bool = True):
    from django.db import connection

    SQL = """
    SELECT schemaname,relname
    FROM pg_stat_all_tables
    WHERE schemaname!='pg_catalog' AND schemaname!='pg_toast';
    """

    if full:
        cmd = 'VACUUM FULL "%s"."%s";'
    else:
        cmd = 'VACUUM "%s"."%s";'

    cursor = connection.cursor()
    cursor.execute(SQL)
    for r in cursor.fetchall():
        print(cmd, r)
        cursor.execute(cmd % (r[0], r[1]))


if __name__ == "__main__":
    from glacier import glacier

    glacier([
        sanity_check_folder_structure,
        import_database,
        import_organism,
        remove_organism,
        remove_missing_organisms,
        reset_database,
        import_pathway_maps,
        sanity_check_postgres,
        import_orthologs,
        send_mail,
        reload_color_css,
        load_blast_dbs,
        update_bokeh,
        load_annotation_descriptions,
        update_taxids,
        backup_genome_similarities,
        import_genome_similarities,
        reload_organism_genomecontents,
        postgres_vacuum
    ])
