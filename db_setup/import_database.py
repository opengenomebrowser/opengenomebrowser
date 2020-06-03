#! /usr/bin/python3
import sys
import os
import json
from progressbar import progressbar  # pip install progressbar2
from colorama import Fore

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import django environment to manipulate the Strain and Member classes
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OpenGenomeBrowser.settings")
from django.core.wsgi import get_wsgi_application
from django.conf import settings

application = get_wsgi_application()

from website.models import Strain, Member, Tag, TaxID, Genome, Gene, KeggMap
from website.models.MemberSerializer import MemberSerializer
from website.models.StrainSerializer import StrainSerializer

from website.models.Annotation import Annotation


class Importer:
    def __init__(self):
        self.db_path = settings.GENOMIC_DATABASE

    def import_database(self, delete_missing=True, auto_delete_missing=False, reload_orthologs=True):
        strains_path = self.db_path + "/strains"
        assert os.path.isdir(strains_path), strains_path

        # Remove Strain or a Member if it has been removed from the database-folder
        if delete_missing:
            self.remove_missing_strains(strains_path, auto_delete_missing)

        # Import new strains / update existing strains
        member_serializer = MemberSerializer()
        strain_serializer = StrainSerializer()

        strain_folders_len = len(list(os.scandir(strains_path)))
        strain_folders = os.scandir(strains_path)

        print("Number of strains to import: {}".format(strain_folders_len))

        for strain_folder in progressbar(strain_folders, max_value=strain_folders_len, redirect_stdout=True):
            current_strain = strain_folder.name
            print(current_strain, end='')

            with open(strain_folder.path + "/strain.json") as file:
                strain_dict = json.loads(file.read())

            assert current_strain == strain_dict["name"], \
                "'name' in strain.json doesn't match folder name: {}".format(strain_folder.path)

            representative_identifier = strain_dict["representative"]
            assert os.path.isdir(strain_folder.path + "/members/" + representative_identifier), \
                "Error: Representative doesn't exist! Strain: {}, Representative: {}" \
                    .format(strain_folder.name, representative_identifier)

            s = strain_serializer.import_strain(strain_dict, update_css=False)

            for member_folder in os.scandir(strain_folder.path + "/members"):
                current_member = member_folder.name
                print("   └── " + current_member, end='')

                with open(member_folder.path + "/member.json") as file:
                    member_dict = json.loads(file.read())

                assert current_member.startswith(strain_folder.name), \
                    "Member name '{}' doesn't start with corresponding strain name '{}'.".format(current_member,
                                                                                                 current_strain)
                assert current_member == member_dict["identifier"], \
                    "'name' in member.json doesn't match folder name: {}".format(member_folder.path)

                is_representative = current_member == representative_identifier

                member_serializer.import_member(member_dict, s, is_representative, update_css=False)

        if reload_orthologs: Annotation.reload_orthofinder()

        Tag.create_tag_color_css()
        TaxID.create_taxid_color_css()

        self.check_invariants()

    def load_kegg_maps(self, reload_data=True, re_render=True):
        from website.models import KeggMap
        KeggMap.load_maps(reload_data=reload_data, re_render=re_render)

    def remove_missing_strains(self, strains_path, auto_delete_missing):
        all_strains = []
        all_members = []

        for strain_folder in os.scandir(strains_path):
            all_strains.append(strain_folder.name)
            for member_folder in os.scandir(strain_folder.path + "/members"):
                all_members.append(member_folder.name)

                # OVERWRITE MEMBER.JSON
                # print(member_folder.name)
                # member_json_path = member_folder.path + "/member.json"
                # assert os.path.isfile(member_json_path)
                # member_dict = MemberSerializer.export_member(member_folder.name)
                # with open(member_json_path, 'w') as file:
                #     file.write(json.dumps(member_dict, indent=4))

                # with open(member_folder.path + "/member.json") as file:
                #     member_dict = json.loads(file.read())
                # # print(member_dict)
                # for file in ['assembly_fasta_file', 'cds_tool_faa_file', 'cds_tool_gbk_file',
                #              'cds_tool_gff_file', 'cds_tool_sqn_file', 'cds_tool_ffn_file']:
                #     if file.startswith('ass'):
                #         folder = '1_assembly'
                #     else:
                #         folder = '2_cds'
                #     fn = member_dict[file + 'name']
                #     del member_dict[file + 'name']
                #     if fn is not None:
                #         fn = F'{folder}/{fn}'
                #     member_dict[file] = fn
                #
                # assert 'custom_annotations' in member_dict
                # cus_ann = member_dict['custom_annotations']
                # for ann in cus_ann:
                #     ann['file'] = '3_annotation/' + ann['file']
                #     assert os.path.isfile(member_folder.path+"/"+ann['file'])
                #
                # print(member_dict['custom_annotations'])
                # for key in member_dict.keys():
                #     assert 'filename' not in key

                # exit(0)

                # with open(member_folder.path + "/member.json", 'w') as file:
                #     file.write(json.dumps(member_dict, indent=4))

        # exit(0)

        for member in Member.objects.all():
            if member.identifier not in all_members:
                if not auto_delete_missing:
                    Importer.print_warning(
                        "Member '{}' is missing from the database-folder. Remove it from the database?"
                            .format(member.identifier), color=Fore.MAGENTA)
                    Importer.confirm_delete(color=Fore.MAGENTA)
                member.delete()

        for strain in Strain.objects.all():
            if strain.name not in all_strains:
                if not auto_delete_missing:
                    Importer.print_warning(
                        "Strain '{}' is missing from the database-folder. Remove it from the database?"
                            .format(strain.name), color=Fore.MAGENTA)
                    Importer.confirm_delete(color=Fore.MAGENTA)
                strain.delete()

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

        for model in [Strain, Member, Tag, TaxID, Genome, Gene, KeggMap, Annotation]:
            model.objects.all().delete()

    @staticmethod
    def check_invariants():
        print()
        print("Checking class invariants...")
        # TaxID and Tag check their own invariants upon saving.
        strains = Strain.objects.all()
        for strain in strains:
            assert strain.invariant(), "Class invariant failed for strain '{}'!".format(strain.name)

        members = Member.objects.all()
        for member in members:
            assert member.invariant(), "Class invariant failed for member '{}'!".format(member.identifier)

        tags = Tag.objects.all()
        for tag in tags:
            assert tag.invariant(), "Class invariant failed for tag '{}'!".format(tag.tag)

        taxids = TaxID.objects.all()
        for taxid in taxids:
            assert taxid.invariant(), "Class invariant failed for TaxID '{} - {}'!".format(taxid.id,
                                                                                           taxid.scientific_name)
        assert Annotation.invariant()

        print("Successfully imported {} strains and {} members, belonging to {} species.".format(
            len(strains), len(members), len(Strain.objects.values('taxid').distinct())))

    # def export_database(self):
    #     for strain in Strain.objects.all()


def main():
    si = Importer()
    # si.reset_database(auto_delete=True)
    si.import_database(auto_delete_missing=False, reload_orthologs=True)
    si.load_kegg_maps(reload_data=False, re_render=False)  # if all false: only recreate KEGG map database entries


if __name__ == "__main__":
    main()
