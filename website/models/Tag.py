import os
from django.db import models
from django.db.models import Q
from django.db.utils import ProgrammingError
from OpenGenomeBrowser import settings
from website.models.helpers import KeyValueStore


class TagManager(models.Manager):
    def create(self, *args, **kwargs):
        from lib.color_generator.ColorGenerator import ColorGenerator

        tag_name = kwargs['tag']
        tag_desciptions = TagDescriptions()
        tag_colors = TagColors()

        if 'description' in kwargs and kwargs['description'] is not None:
            tag_desciptions.set_key(key=tag_name, value=kwargs['description'])
        else:
            try:
                description = tag_desciptions.get_key(key=tag_name)
            except KeyError:
                description = '-'
                tag_desciptions.set_key(key=tag_name, value=description)
            kwargs['description'] = description

        color_string = tag_colors.get_or_generate_color(key=tag_name)
        color_int = ColorGenerator.import_string(color_string)

        text_color_white = ColorGenerator.is_dark(color_int=color_int, is_float=False)

        kwargs['color'] = color_string
        kwargs['text_color_white'] = text_color_white

        return super(TagManager, self).create(*args, **kwargs)

    def get_or_create(self, tag: str, description=None):
        try:
            tag_obj = Tag.objects.get(tag=tag)
        except Tag.DoesNotExist:
            tag_obj = Tag.objects.create(tag=tag, description=description)
        return tag_obj


class Tag(models.Model):
    """
    Tags for organisms
    """

    objects = TagManager()

    tag = models.CharField(max_length=150, primary_key=True)
    description = models.TextField(blank=True)

    color = models.CharField(max_length=11)
    text_color_white = models.BooleanField()  # True == white, False == black

    def natural_key(self):
        return self.tag

    @property
    def html(self):
        return f'<span class="tag ogb-tag" data-tag="{self.obj.tag}" title="{self.description}">@tag:{self.tag}</span>'

    def get_html_badge(self):
        return f'<span class="ogb-tag" data-tag="{self.tag}">{self.tag}</span>'

    @staticmethod
    def getTagList() -> [str]:
        try:
            return [tag.tag for tag in Tag.objects.all()]
        except ProgrammingError:
            print("this should only happen during database setup! see website/models/Tag.getTagList()")
            return ""

    def get_child_genomes(self, representative=None, contaminated=None, restricted=None):
        from .Genome import Genome
        qs = Genome.objects.filter(Q(tags=self.tag) | Q(organism__tags=self.tag))

        if representative is not None:
            qs = qs.filter(representative__isnull=not representative)
        if contaminated is not None:
            qs = qs.filter(contaminated=contaminated)
        if restricted is not None:
            qs = qs.filter(organism__restricted=restricted)

        return qs.distinct()

    @property
    def css(self):
        return f'[data-tag="{self.tag}"] {{background-color: rgb({self.color}) !important; color: {"white" if self.text_color_white else "black"} !important}}'

    @staticmethod
    def get_tag_css_paths():
        files = [
            os.path.abspath(F'{settings.BASE_DIR}/website/static/global/css/tag_color.css'),
            os.path.abspath(F'{settings.BASE_DIR}/static_root/global/css/tag_color.css')
        ]
        for file in files:
            # ensure parent folder exists
            os.makedirs(os.path.dirname(file), exist_ok=True)
        return files

    @staticmethod
    def create_tag_color_css():
        css = '\n'.join(tag.css for tag in Tag.objects.all())
        for file in Tag.get_tag_css_paths():
            with open(file, 'w') as f:
                f.write(css)

    def __str__(self):
        return self.tag

    def invariant(self):
        # currently nothing to check
        return True


class TagDescriptions(KeyValueStore):
    _file = F'{settings.GENOMIC_DATABASE}/tag_to_description.json'
    _model = Tag
    _key = 'tag'
    _value = 'description'


class TagColors(KeyValueStore):
    _file = F'{settings.GENOMIC_DATABASE}/tag_to_color.json'
    _model = Tag
    _key = 'tag'
    _value = 'color'

    def get_or_generate_key(self, key):
        try:
            return self.get_key(key)
        except KeyError:
            from lib.color_generator.ColorGenerator import ColorGenerator
            color_float = ColorGenerator.generate_new_color_bright(
                brightness=1000,
                existing_colors=[ColorGenerator.import_string(c) for c in self.get_dict().values()],
                n_iter=1000
            )
            color_int = ColorGenerator.color_to_int(color_float)
            color = ','.join([str(c) for c in color_int])
            self.set_key(key, value=color)
            return color
