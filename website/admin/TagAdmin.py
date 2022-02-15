import json

from django.contrib.admin import ModelAdmin
from django.contrib import messages
from django.db import transaction

from website.models import Tag, TagDescriptions
from django.http import HttpResponseRedirect

from website.serializers import GenomeSerializer, OrganismSerializer


class TagAdmin(ModelAdmin):
    search_fields = ['tag']

    exclude = ['color', 'text_color_white']

    def save_model(self, request, obj: Tag, form, change):
        # to change the tag name, the change would have to be propagated to all metadata json files!
        if 'tag' in form.initial and form.initial['tag'] != form.cleaned_data['tag']:
            old_name = form.initial['tag']
            old_tag = Tag.objects.get(tag=old_name)
            new_name = form.cleaned_data['tag']
            new_description = form.cleaned_data['description']

            if Tag.objects.filter(tag=new_name).exists():
                raise AssertionError(f'A tag with the name {new_name} already exists!')

            new_tag = Tag.objects.create(tag=new_name, description=new_description)

            n_genomes_updated = 0
            for genome in old_tag.genome_set.all():
                with transaction.atomic():
                    with open(genome.metadata_json) as f:
                        data = json.load(f)
                    data['tags'] = [t for t in data['tags'] if t != old_name] + [new_name]
                    GenomeSerializer.update_metadata_json(
                        genome=genome, new_data=data, who_did_it=request.user.username
                    )
                    new_tag.genome_set.add(genome)
                    old_tag.genome_set.remove(genome)
                n_genomes_updated += 1

            n_organisms_updated = 0
            for organism in old_tag.organism_set.all():
                with transaction.atomic():
                    with open(organism.metadata_json) as f:
                        data = json.load(f)
                    data['tags'] = [t for t in data['tags'] if t != old_name] + [new_name]
                    OrganismSerializer.update_metadata_json(
                        organism=organism, new_data=data, who_did_it=request.user.username
                    )
                    new_tag.organism_set.add(organism)
                    old_tag.organism_set.remove(organism)

                n_organisms_updated += 1

            assert old_tag.organism_set.count() == old_tag.genome_set.count() == 0
            old_tag.delete()
            obj = new_tag

            messages.add_message(
                request, messages.SUCCESS,
                f'Replaced tag {old_name} with {new_name} '
                f'for {n_organisms_updated} organisms and {n_genomes_updated} genomes!'
            )

        try:
            tag_obj = Tag.objects.get(pk=obj.pk)
            # object exists: save and write key to dictionary
            super().save_model(request, obj, form, change)
            TagDescriptions().set_key(key=obj.tag, value=obj.description)
            messages.add_message(request, messages.INFO, 'Changed tag.')
        except Tag.DoesNotExist:
            tag_obj = Tag.objects.create(tag=obj.tag, description=obj.description)
            messages.add_message(request, messages.INFO, 'Created new tag.')

        Tag.create_tag_color_css()

    def changeform_view(self, request, *args, **kwargs):
        try:
            return super().changeform_view(request, *args, **kwargs)
        except Exception as e:
            messages.add_message(request, messages.ERROR, f'Something went wrong: {str(e)}')
            return HttpResponseRedirect(request.path)

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return super().has_delete_permission(request, obj)

        has_error = False

        if obj.genome_set.count() > 0:
            messages.add_message(request, messages.WARNING,
                                 f'There are genomes that have this tag ({obj.tag})! Cannot delete.')
            has_error = True

        if obj.organism_set.count() > 0:
            messages.add_message(request, messages.WARNING,
                                 f'There are organisms that have this tag ({obj.tag})! Cannot delete.')
            has_error = True

        if has_error:
            return False
        else:
            return super().has_delete_permission(request, obj)
