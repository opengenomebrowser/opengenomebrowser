from django.db import models
from django.db.models import Q
from django.db.utils import ProgrammingError
from OpenGenomeBrowser import settings
import json
import os


class TagManager(models.Manager):
    def create(self, *args, **kwargs):
        tag_name = kwargs['tag']

        if 'description' in kwargs and kwargs['description'] is not None:
            tag_desciptions.set_key(key=tag_name, value=kwargs['description'])
        else:
            try:
                description = tag_desciptions.get_key(key=tag_name)
            except KeyError:
                description = '-'
                tag_desciptions.set_key(key=tag_name, value=description)
            kwargs['description'] = description

        from lib.tax_id_to_color.glasbey_wrapper import GlasbeyWrapper
        color, text_color_white = GlasbeyWrapper.get_color_from_tag(tag=tag_name)

        kwargs['color'] = color
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
        return f'<div class="tag ogb-tag" data-tag="{self.obj.tag}" title="{self.description}">@tag:{self.tag}</div>'

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


class TagDescriptions:
    def __init__(self):
        self.description_file = F'{settings.GENOMIC_DATABASE}/tag_to_description.json'
        if not os.path.isfile(self.description_file):
            json.dump({}, open(self.description_file, 'w'))

    def get_dict(self) -> dict:
        if os.path.isfile(self.description_file):
            return json.load(open(self.description_file))
        return {}

    def get_key(self, key) -> str:
        tmp_dict = self.get_dict()
        return tmp_dict[key]

    def set_key(self, key, value):
        tmp_dict = self.get_dict()
        tmp_dict[key] = value
        json.dump(tmp_dict, open(self.description_file, 'w'), indent=4)


tag_desciptions = TagDescriptions()
