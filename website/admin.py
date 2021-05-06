from django.contrib import admin
from django.urls import path
from django.db.models import JSONField
from django.contrib import messages
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from website.models.helpers.backup_file import read_file_or_default, overwrite_with_backup
from website.models import Organism, Genome, Tag, TagDescriptions
from website.serializers import OrganismSerializer
from website.serializers import GenomeSerializer
from prettyjson import PrettyJSONWidget
import json
from dictdiffer import diff
from datetime import date


class MarkdownObject:
    def __init__(self, type: str, name: str, file_path: str, featured_on: str):
        self.type = type
        self.name = name
        self.file_path = file_path
        self.featured_on = featured_on

    @property
    def markdown(self):
        return read_file_or_default(file=f'database/{self.file_path}', default='')

    def set_markdown(self, md: str, user: str):
        self.obj.set_markdown(md=md, user=user)


class MarkdownObjectOrganism(MarkdownObject):
    def __init__(self, organism: Organism):
        self.obj = organism
        super().__init__(
            type='organism', name=organism.name, file_path=organism.markdown_path(relative=True), featured_on=f'/organism/{organism.name}'
        )


class MarkdownObjectGenome(MarkdownObject):
    def __init__(self, genome: Genome):
        self.obj = genome
        super().__init__(
            type='organism', name=genome.identifier, file_path=genome.markdown_path(relative=True), featured_on=f'/genome/{genome.identifier}'
        )


class MarkdownObjectPage(MarkdownObject):
    def __init__(self, page: str):
        self.page = page
        if page == 'index':
            super().__init__(
                type='page', name='index', file_path='/index.md', featured_on='/'
            )
        else:
            raise KeyError(f'Error: page does not exist: {page}.')

    def set_markdown(self, md: str, user: str):
        from OpenGenomeBrowser.settings import GENOMIC_DATABASE
        overwrite_with_backup(file=f'{GENOMIC_DATABASE}/{self.file_path}', content=md, user=user, delete_if_empty=True)


class OgbAdmin(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(r'markdown-editor/', self.admin_view(self.markdown_editor), name='markdown_editor'),
            path(r'markdown-editor/submit/', self.admin_view(self.markdown_submit), name='markdown_editor')
        ]
        urls = custom_urls + urls
        return urls

    def markdown_editor(self, request):
        context = dict(
            title='Markdown Editor',
            error_danger=[], error_warning=[], error_info=[],
            genomes=[],
            genome_to_species={}
        )

        try:
            if 'page' in request.GET:
                try:
                    context['obj'] = MarkdownObjectPage(page=request.GET['page'])
                except KeyError as e:
                    context['error_danger'].append(str(e))
            elif 'genome' in request.GET:
                context['obj'] = MarkdownObjectGenome(genome=Genome.objects.get(identifier=request.GET['genome']))
            elif 'organism' in request.GET:
                context['obj'] = MarkdownObjectOrganism(organism=Organism.objects.get(name=request.GET['organism']))
            else:
                context['error_danger'].append('Error: no page, genome or organism specified.')
        except ObjectDoesNotExist:
            context['error_danger'].append('Error: could not find object in database.')

        return render(request, 'admin/markdown-editor.html', context)

    def markdown_submit(self, request):
        type = request.POST['type']
        name = request.POST['name']
        markdown = request.POST['markdown']
        user = request.user.username

        if type == 'page':
            obj = MarkdownObjectPage(page=name)
        elif type == 'genome':
            obj = MarkdownObjectGenome(Genome.objects.get(identifier=name))
        elif type == 'organism':
            obj = MarkdownObjectOrganism(Organism.objects.get(name=name))
        else:
            return JsonResponse(dict(message='Type not supported!'), status=400)

        obj.set_markdown(md=markdown, user=user)

        return JsonResponse(dict(success=True))


ogb_admin = OgbAdmin()

ogb_admin.register(User, UserAdmin)
ogb_admin.register(Group, GroupAdmin)


class TagAdmin(admin.ModelAdmin):
    search_fields = ['tag']

    exclude = ['color', 'text_color_white']

    def save_model(self, request, obj: Tag, form, change):
        # to change the tag name, the change would have to be propagated to all metadata json files!
        if 'tag' in form.initial and form.initial['tag'] != form.cleaned_data['tag']:
            messages.warning(request, messages.INFO, F'Changing tag names is currently not supported.')
            return

        try:
            tag_obj = Tag.objects.get(pk=obj.pk)
            # object exists: save and write key to dictionary
            super().save_model(request, obj, form, change)
            TagDescriptions().set_key(key=obj.tag, value=obj.description)
            messages.add_message(request, messages.INFO, 'Changed tag.')
        except Tag.DoesNotExist:
            tag_obj = Tag.objects.create(tag=obj.tag, description=obj.description)
            messages.add_message(request, messages.INFO, 'Created new tag.')
        except Exception as e:
            messages.add_message(request, messages.ERROR, f'Something went wrong: {str(e)}')

        Tag.create_tag_color_css()


ogb_admin.register(Tag, TagAdmin)


class OrganismAdmin(admin.ModelAdmin):
    change_form_template = 'admin/change_form_organism.html'  # todo: does not have an effect

    search_fields = ['name']

    readonly_fields = ['name']

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    def render_change_form(self, request, context, *args, **kwargs):
        # ensure only genomes that belong to organism may be chosen.
        organism = kwargs['obj']
        context['adminform'].form.fields['representative'].queryset = Genome.objects.filter(organism=organism)
        return super().render_change_form(request, context, *args, **kwargs)

    def save_model(self, request, obj: Organism, form, change):
        # turn form into organism.json
        json_data = form.cleaned_data.copy()
        json_data['name'] = obj.name
        json_data['tags'] = set(t.tag for t in json_data['tags'])
        json_data['taxid'] = json_data['taxid'].id
        json_data['representative'] = json_data['representative'].identifier

        # ensure that representative genome exists and belongs to organism
        try:
            r = Genome.objects.get(identifier=json_data['representative'])
            assert r.organism.name == obj.name
        except Genome.DoesNotExist:
            messages.add_message(request, messages.INFO, F'Representative ({json_data["representative"]}) does not exist!')
            return
        except AssertionError:
            messages.add_message(request, messages.INFO, F'Representative ({json_data["representative"]}) does not belong to this organism!')
            return

        # load current json, turn tags into set
        old_dict = json.load(open(obj.metadata_json))
        old_dict['tags'] = set(old_dict['tags'])

        # did something change?
        difference = list(diff(json_data, old_dict))
        match = len(difference) == 0

        if match:
            messages.add_message(request, messages.INFO, 'No difference!')
        else:
            messages.add_message(request, messages.INFO, F'Saving the following change: {difference}')
            super().save_model(request, obj, form, change)

            try:
                OrganismSerializer.update_metadata_json(organism=obj, new_data=json_data, who_did_it=request.user.username)
            except Exception as e:
                messages.add_message(request, messages.ERROR, f'Failed to edit the json file! {str(e)}')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


ogb_admin.register(Organism, OrganismAdmin)


class GenomeAdmin(admin.ModelAdmin):
    change_form_template = 'admin/change_form_genome.html'  # todo: does not have an effect

    search_fields = ['identifier']

    readonly_fields = ['identifier',
                       'cds_tool_faa_file',
                       'cds_tool_gbk_file',
                       'cds_tool_gff_file',
                       'cds_tool_ffn_file',
                       'cds_tool_sqn_file',
                       'custom_annotations',
                       'assembly_fasta_file',
                       'BUSCO'
                       ]

    exclude = [
        'genomecontent', 'organism',  # primary key, foreign keys
        'assembly_gc', 'assembly_longest_scf', 'assembly_size', 'assembly_nr_scaffolds',  # calculated automatically
        'assembly_n50', 'assembly_gaps', 'assembly_ncount', 'BUSCO_percent_single'  # calculated automatically
    ]

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    def save_model(self, request, obj: Genome, form, change):
        # turn form into organism.json
        json_data = form.cleaned_data.copy()
        json_data['tags'] = set(t.tag for t in json_data['tags'])
        for field in self.readonly_fields:
            assert field not in json_data
            json_data[field] = getattr(obj, field)
        for field, data in json_data.items():
            if type(data) is date:
                # convert dates in to strings
                json_data[field] = str(data)

        from db_setup.check_metadata import genome_metadata_is_valid
        try:
            assert genome_metadata_is_valid(data=json_data, path_to_genome=obj.base_path(relative=False),
                                            raise_exception=True), 'check_metadata raised an error'
        except Exception as e:
            messages.add_message(request, messages.INFO, F'Something is wrong with your data: {str(e)}')
            return

        # load current json, turn tags into set
        old_dict = json.load(open(obj.metadata_json))
        old_dict['tags'] = set(old_dict['tags'])

        # did something change?
        difference = list(diff(json_data, old_dict))
        match = len(difference) == 0

        if match:
            messages.add_message(request, messages.INFO, 'No difference!')
        else:
            messages.add_message(request, messages.INFO, F'Saving the following change: {difference}')
            super().save_model(request, obj, form, change)

            try:
                GenomeSerializer.update_metadata_json(genome=obj, new_data=json_data, who_did_it=request.user.username)
            except Exception as e:
                messages.add_message(request, messages.ERROR, f'Failed to edit the json file! {str(e)}')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


ogb_admin.register(Genome, GenomeAdmin)
