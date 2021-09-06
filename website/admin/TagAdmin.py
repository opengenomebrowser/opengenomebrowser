from django.contrib.admin import ModelAdmin
from django.contrib import messages

from website.models import Tag, TagDescriptions
from django.http import HttpResponseRedirect


class TagAdmin(ModelAdmin):
    search_fields = ['tag']

    exclude = ['color', 'text_color_white']

    def save_model(self, request, obj: Tag, form, change):
        # to change the tag name, the change would have to be propagated to all metadata json files!
        if 'tag' in form.initial and form.initial['tag'] != form.cleaned_data['tag']:
            raise AssertionError(f'Changing tag names is currently not supported.')

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
