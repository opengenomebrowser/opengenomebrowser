import logging
import os
import shutil
from tempfile import TemporaryDirectory

from django import forms
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.http import JsonResponse

from OpenGenomeBrowser.settings import GENOMIC_DATABASE
from website.models import Organism, Genome

from opengenomebrowser_tools.import_genome import import_genome as import_genome_into_folder_structure
from db_setup.manage_ogb import import_organism as import_organism_to_database
from db_setup.manage_ogb import remove_organism as remove_organism_from_database

from subprocess import run, PIPE


class GenomeUploadForm(forms.Form):
    organism_name = forms.CharField(label='Desired organism name', max_length=40)
    genome_identifier = forms.CharField(label='Desired genome identifier', max_length=50)
    rename = forms.BooleanField(label='Must the files be renamed?', initial=False, required=False)
    genome_files = forms.FileField(
        label='Genomic files (at least .ffn, .gbk, .gff)',
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()

        organism_name = cleaned_data.get('organism_name')
        genome_identifier = cleaned_data.get('genome_identifier')

        if Organism.objects.filter(name=organism_name).exists():
            self.add_error('organism_name', f'Organism already exists: {organism_name}')

        if Genome.objects.filter(identifier=genome_identifier).exists():
            self.add_error('genome_identifier', f'Genome already exists: {genome_identifier}')

        if not genome_identifier.startswith(organism_name):
            msg = 'Genome identifier must start with organism name!'
            self.add_error('organism_name', msg)
            self.add_error('genome_identifier', msg)

        return cleaned_data


class GenomeUploadView(FormView):
    form_class = GenomeUploadForm
    template_name = 'admin/genome_upload.html'  # Replace with your template(which you created)
    success_url = None  # to be changed later

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if not form.is_valid():
            return self.form_invalid(form)

        organism_name = form.cleaned_data['organism_name']

        organism_folder = f'{GENOMIC_DATABASE}/organisms/{organism_name}'
        if os.path.isdir(organism_folder):
            form.add_error(None, f'Cannot proceed: {organism_folder=} already exists!')
            return self.form_invalid(form)

        genome_identifier = form.cleaned_data['genome_identifier']
        rename = form.cleaned_data['rename']
        assert type(rename) is bool, str(type(rename))
        genome_files = request.FILES.getlist('genome_files')

        print(f'Submission of new genomes: {organism_name} :: {genome_identifier}')
        with TemporaryDirectory() as tempdir:
            key_files = [f'{genome_identifier}.{suffix}' for suffix in ('gbk', 'gff', 'fna')]
            for file in genome_files:
                assert file.name not in key_files, f'Error: Two files with same name: {file.name}'
                os.symlink(src=file.file.name, dst=f'{tempdir}/{file.name}')
            try:
                print(f'Import into folder_structure: {organism_name} :: {genome_identifier}')
                import_genome_into_folder_structure(
                    import_dir=tempdir, database_dir=GENOMIC_DATABASE,
                    organism=organism_name, genome=genome_identifier,
                    rename=rename,
                    check_files=True,
                    import_settings=None
                )
            except Exception as e:
                # undo putative changes to folder structure
                if os.path.isdir(organism_folder):
                    shutil.rmtree(organism_folder)

                msg = f'Failed to add files to folder structure: {e}'
                logging.warning(msg)
                form.add_error(None, msg)
                return self.form_invalid(form)

            self.success_url = f'/admin/genome-import/{organism_name}/'
            print(f'Successfully imported: {organism_name} :: {genome_identifier}')
            return self.form_valid(form)


def genome_import_view(request, slug: str):
    context = dict(
        title='Genome import',
        error_danger=[], error_warning=[], error_info=[]
    )
    organism_name = slug
    context['organism'] = organism_name

    organism_folder = f'{GENOMIC_DATABASE}/organisms/{organism_name}'
    context['organism_folder_rel'] = f'organisms/{organism_name}'

    if Organism.objects.filter(name=organism_name).exists():
        context['organism_in_database'] = True

    if os.path.isdir(organism_folder):
        context['organism_folder_exists'] = True
        context['tree'] = run(['tree', organism_folder], stdout=PIPE, encoding='utf-8').stdout

    # make sure organism is not in db yet and folder exists
    if not os.path.isdir(organism_folder):
        context['error_danger'].append(f'Error: Folder does not exist: {organism_folder}.')
    if Organism.objects.filter(name=organism_name).exists():
        context['error_warning'].append(f'Warning: Organism with name={organism_name} has already been imported into the database.')

    return render(request, 'admin/genome_import.html', context=context)


def genome_import_submit(request):
    organism_name = request.POST.get('organism')

    try:
        print(f'Import into database: organism={organism_name}')
        import_organism_to_database(name=organism_name)  # note: this function is atomic
    except Exception as e:
        # no need to undo db changes here, as import_organism is atomic
        msg = f'Failed to load files into the database: {e}'
        logging.warning(msg)
        return JsonResponse(dict(success='false', message=msg), status=500)

    o = Organism.objects.get(name=organism_name)  # ensure it exists
    g = o.genome_set.first()

    return JsonResponse(dict(
        success='true',
        message=f'Successfully imported organism={o.name} and genome={g.identifier}.\n\n'
                f'Click here to edit <a href="/admin/website/organism/{o.pk}/">organism.json</a>\n'
                f'Click here to edit <a href="/admin/website/genome/{g.pk}/">genome.json</a>'
    ))


def remove_genome(request):
    organism_name = request.POST.get('organism')
    assert '/' not in organism_name

    for permission in ['website.delete_genome', 'website.delete_organism']:
        if not request.user.has_perm(permission):
            return JsonResponse(dict(success='false', message=f'You lack the {permission} permission.'), status=500)

    organism_folder = f'{GENOMIC_DATABASE}/organisms/{organism_name}'

    if not os.path.isdir(organism_folder):
        return JsonResponse(dict(success='false', message=f'Organism folder does not exist: {organism_folder}'), status=500)

    try:
        if Organism.objects.filter(name=organism_name).exists():
            remove_organism_from_database(name=organism_name)
    except Exception as e:
        msg = f'Failed to remove organism={organism_name} from database: {e}'
        logging.warning(msg)
        return JsonResponse(dict(success='false', message=msg), status=500)

    try:
        shutil.rmtree(organism_folder)
    except Exception as e:
        msg = f'Failed to remove organism={organism_name} from folder structure: {e}'
        logging.warning(msg)
        return JsonResponse(dict(success='false', message=msg), status=500)

    return JsonResponse(dict(
        success='true',
        message=f'Successfully removed organism={organism_name}'
    ))
