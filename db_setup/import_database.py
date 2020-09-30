#! /usr/bin/python3
import sys
import os
import json
from progressbar import progressbar  # pip install progressbar2
from colorama import Fore

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import django environment to manipulate the Organism and Genome classes
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OpenGenomeBrowser.settings")
from django.core.wsgi import get_wsgi_application
from django.conf import settings

application = get_wsgi_application()

from website.models import Organism, Genome, Tag, TaxID, GenomeContent, Gene, PathwayMap
from website.models.GenomeSerializer import GenomeSerializer
from website.models.OrganismSerializer import OrganismSerializer

from website.models.Annotation import Annotation


class Importer:
    def __init__(self):
        self.db_path = settings.GENOMIC_DATABASE

    def import_database(self, delete_missing=True, auto_delete_missing=False, reload_orthologs=True):
        organisms_path = self.db_path + "/organisms"
        assert os.path.isdir(organisms_path), organisms_path

        # Remove Organism or a Genome if it has been removed from the database-folder
        if delete_missing:
            self.remove_missing_organisms(organisms_path, auto_delete_missing)

        # Import new organisms / update existing organisms
        genome_serializer = GenomeSerializer()
        organism_serializer = OrganismSerializer()

        organism_folders_len = len(list(os.scandir(organisms_path)))
        organism_folders = os.scandir(organisms_path)

        print(F"Number of organisms to import: {organism_folders_len}")

        for organism_folder in progressbar(organism_folders, max_value=organism_folders_len, redirect_stdout=True):
            current_organism = organism_folder.name
            print(current_organism, end='')

            with open(organism_folder.path + "/organism.json") as file:
                organism_dict = json.loads(file.read())

            assert current_organism == organism_dict["name"], \
                F"'name' in organism.json doesn't match folder name: {organism_folder.path}"

            representative_identifier = organism_dict["representative"]
            assert os.path.isdir(organism_folder.path + "/genomes/" + representative_identifier), \
                F"Error: Representative doesn't exist! Organism: {organism_folder.name}, Representative: {representative_identifier}"

            s = organism_serializer.import_organism(organism_dict, update_css=False)

            for genome_folder in os.scandir(organism_folder.path + "/genomes"):
                current_genome = genome_folder.name
                print("   └── " + current_genome, end='')

                with open(genome_folder.path + "/genome.json") as file:
                    genome_dict = json.loads(file.read())

                assert current_genome.startswith(organism_folder.name), \
                    F"genome name '{current_genome}' doesn't start with corresponding organism name '{current_organism}'."
                assert current_genome == genome_dict["identifier"], \
                    F"'name' in genome.json doesn't match folder name: {genome_folder.path}"

                is_representative = current_genome == representative_identifier

                genome_serializer.import_genome(genome_dict, s, is_representative, update_css=False)

        if reload_orthologs:
            Annotation.reload_orthofinder()

        Tag.create_tag_color_css()
        TaxID.create_taxid_color_css()

        self.check_invariants()

    def reload_pathway_maps(self):
        from website.models import PathwayMap
        PathwayMap.reload_maps()

    def remove_missing_organisms(self, organisms_path, auto_delete_missing):
        all_organisms = []
        all_genomes = []

        for organism_folder in os.scandir(organisms_path):
            all_organisms.append(organism_folder.name)
            for genome_folder in os.scandir(organism_folder.path + "/genomes"):
                all_genomes.append(genome_folder.name)

        for genome in Genome.objects.all():
            if genome.identifier not in all_genomes:
                if not auto_delete_missing:
                    Importer.print_warning(
                        F"Genome '{genome.identifier}' is missing from the database-folder. Remove it from the database?", color=Fore.MAGENTA)
                    Importer.confirm_delete(color=Fore.MAGENTA)
                genome.delete()

        for organism in Organism.objects.all():
            if organism.name not in all_organisms:
                if not auto_delete_missing:
                    Importer.print_warning(
                        F"Organism '{organism.name}' is missing from the database-folder. Remove it from the database?", color=Fore.MAGENTA)
                    Importer.confirm_delete(color=Fore.MAGENTA)
                organism.delete()

    @staticmethod
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

    @staticmethod
    def print_warning(message, color):
        if bool(True):
            print(color + message)
            print(Fore.BLACK + '', end='')

    @staticmethod
    def reset_database(auto_delete=False):
        print('Resetting database...')
        if not auto_delete:
            Importer.print_warning("DO YOU REALLY WANT TO RESET THE DATABASE?", color=Fore.MAGENTA)
            Importer.confirm_delete(color=Fore.MAGENTA)

        for model in [Organism, Genome, Tag, TaxID, GenomeContent, Gene, PathwayMap, Annotation]:
            model.objects.all().delete()

    @staticmethod
    def check_invariants():
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

    # def export_database(self):
    #     for organism in Organism.objects.all()


def main():
    si = Importer()
    # si.reset_database(auto_delete=True)
    si.import_database(auto_delete_missing=False, reload_orthologs=False)
    # si.reload_pathway_maps()

    # TODO: hook install_orthofinder.py
    # TODO: hook notice if oat is missing


if __name__ == "__main__":
    main()
