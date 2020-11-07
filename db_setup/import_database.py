#! /usr/bin/python3
import sys
import os
import json
from progressbar import progressbar  # pip install progressbar2
from colorama import Fore
import bokeh
import requests

OGB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(OGB_DIR)

# import django environment to manipulate the Organism and Genome classes
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OpenGenomeBrowser.settings")
from django.core.wsgi import get_wsgi_application
from django.conf import settings

application = get_wsgi_application()

from website.models import Organism, Genome, Tag, TaxID, GenomeContent, Gene, PathwayMap
from website.serializers import GenomeSerializer
from website.serializers import OrganismSerializer

from website.models.Annotation import Annotation

ORGANISMS_PATH = settings.GENOMIC_DATABASE + "/organisms"


def print_warning(message, color):
    if bool(True):
        print(color + message)
        print(Fore.BLACK + '', end='')


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

    print(color + '', end='')
    while (True):
        inp = yes_or_no()
        if inp is None:
            continue
        elif inp is True:
            print(Fore.BLACK + 'removing...', end='')
        elif inp is False:
            print(Fore.BLACK + "quit program")
            exit(0)
        break


def import_database(delete_missing: bool = True, auto_delete_missing: bool = False):
    """
    Load organisms and genomes from file database into PostgreSQL database

    :param delete_missing: if True (default), check if organisms/genomes have gone missing
    :param auto_delete_missing: if True, remove missing organisms/genomes without console prompt
    """
    assert os.path.isdir(ORGANISMS_PATH), ORGANISMS_PATH

    # Remove Organism or a Genome if it has been removed from the database-folder
    if delete_missing:
        remove_missing_organisms(auto_delete_missing)

    # Import new organisms / update existing organisms
    organism_folders_len = len(list(os.scandir(ORGANISMS_PATH)))
    organism_folders = os.scandir(ORGANISMS_PATH)

    print(F"Number of organisms to import: {organism_folders_len}")

    for organism_folder in progressbar(organism_folders, max_value=organism_folders_len, redirect_stdout=True):
        current_organism = organism_folder.name
        print(current_organism, end='')

        if os.path.isfile(F'{organism_folder.path}/.ignore'):
            print(' :: ignored')
            continue

        with open(F'{organism_folder.path}/organism.json') as file:
            organism_dict = json.loads(file.read())

        assert current_organism == organism_dict["name"], \
            F"'name' in organism.json doesn't match folder name: {organism_folder.path}"

        representative_identifier = organism_dict["representative"]
        assert os.path.isdir(F'{organism_folder.path}/genomes/{representative_identifier}'), \
            F"Error: Representative doesn't exist! Organism: {current_organism}, Representative: {representative_identifier}"
        assert not os.path.isfile(F'{organism_folder.path}/genomes/{representative_identifier}/.ignore'), \
            F"Error: Representative is ignored! Organism: {current_organism}, Representative: {representative_identifier}"

        organism_serializer = OrganismSerializer(data=organism_dict)

        organism_serializer.is_valid(raise_exception=True)
        # s = organism_serializer.import_organism(organism_dict, update_css=False)
        try:
            o = Organism.objects.get(name=current_organism)
            match, difference = OrganismSerializer.json_matches_organism(o, organism_dict)
            if match:
                print(' :: unchanged')

            else:
                print(F' :: update: {difference}')
                o = organism_serializer.update(instance=o, validated_data=organism_serializer.validated_data, representative_isnull=True)

        except Organism.DoesNotExist:
            print(' :: new')
            o = organism_serializer.create(organism_serializer.validated_data)

        genomes = []

        for genome_folder in os.scandir(F'{organism_folder.path}/genomes'):
            current_genome = genome_folder.name
            print("   └── " + current_genome, end='')

            if os.path.isfile(F'{genome_folder.path}/.ignore'):
                print(' :: ignored')
                continue

            with open(F'{genome_folder.path}/genome.json') as file:
                genome_dict = json.loads(file.read())

            assert current_genome.startswith(current_organism), \
                F"genome name '{current_genome}' doesn't start with corresponding organism name '{current_organism}'."
            assert current_genome == genome_dict["identifier"], \
                F"'name' in genome.json doesn't match folder name: {genome_folder.path}"

            genome_serializer = GenomeSerializer(data=genome_dict)
            genome_serializer.is_valid(raise_exception=True)

            try:
                g = Genome.objects.get(identifier=current_genome)
                match, difference = GenomeSerializer.json_matches_genome(g, genome_dict, organism_name=o.name)
                if match:
                    print(' :: unchanged')

                else:
                    print(F' :: update: {difference}')
                    g = genome_serializer.update(instance=g, validated_data=genome_serializer.validated_data, organism=o)

            except Genome.DoesNotExist:
                print(' :: new')
                g = genome_serializer.create(genome_serializer.validated_data, organism=o)

            genomes.append(g)


        o.representative = Genome.objects.get(identifier=representative_identifier)
        o.save()

        for g in genomes:
            GenomeSerializer.update_genomecontent(g)

    Tag.create_tag_color_css()
    TaxID.create_taxid_color_css()

    check_invariants()


def reload_pathway_maps():
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
    all_organisms = []
    all_genomes = []

    for organism_folder in os.scandir(ORGANISMS_PATH):
        if not os.path.isfile(F'{organism_folder.path}/.ignore'):
            all_organisms.append(organism_folder.name)
        for genome_folder in os.scandir(organism_folder.path + "/genomes"):
            if not os.path.isfile(F'{genome_folder.path}/.ignore'):
                all_genomes.append(genome_folder.name)

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


def check_invariants():
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


def reload_orthologs(auto_delete: bool = False):
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
    url_fill = F'-{bokeh_version}'

    if not auto_delete:
        print_warning(
            F'Overwrite bokeh js files? (New version: {bokeh_version})',
            color=Fore.MAGENTA
        )
        confirm_delete(color=Fore.MAGENTA)
        print()

    cdn = 'https://cdn.bokeh.org/bokeh/release'
    js_dir = F'{OGB_DIR}/website/static/global/js'
    files = ['bokeh{}.min.js', 'bokeh-widgets{}.min.js', 'bokeh-tables{}.min.js', 'bokeh-api{}.min.js']

    for file in files:
        url = F'{cdn}/{file.format(url_fill)}'
        target_path = F'{js_dir}/{file.format("")}'
        print(F'{url}  -->>  {target_path}')
        r = requests.get(url, allow_redirects=True)

        with open(target_path, 'wb') as f:
            f.write(r.content)

    print('\nRemember to run "python manage.py collectstatic"!')


if __name__ == "__main__":
    from glacier import glacier

    glacier([
        import_database,
        reset_database,
        remove_missing_organisms,
        reload_pathway_maps,
        check_invariants,
        reload_orthologs,
        update_bokeh
    ])
