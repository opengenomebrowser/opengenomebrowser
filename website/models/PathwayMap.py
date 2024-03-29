import os
import json
import bs4
from django.utils.text import slugify
from django.db import models
from website.models.Annotation import Annotation
from website.models.GenomeContent import add_many_annotations
from OpenGenomeBrowser import settings


class PathwayMap(models.Model):
    """
    Represents a Pathway map.

    Import maps from settings.PATHWAY_MAPS
    """

    slug = models.SlugField(max_length=200, primary_key=True)

    title = models.CharField(max_length=200)

    filename = models.CharField(max_length=200, unique=True)

    annotations = models.ManyToManyField(Annotation)

    def __str__(self):
        return f'{self.slug} : {self.title}'

    @property
    def svg(self) -> str:
        with open(f'{settings.PATHWAY_MAPS}/{self.filename}') as f:
            return f.read()
    @property
    def html(self):
        return f'<span class="ogb-tag pathway" title="{self.title}">{self.slug}</span>'

    @staticmethod
    def _get_type_dict():
        if settings.PATHWAY_MAPS_TYPE_DICT:
            return json.load(open(settings.PATHWAY_MAPS_TYPE_DICT))
        else:
            print('default type dict')
            type_dict = {a.label: a.value for a in Annotation.AnnotationTypes}
            return type_dict

    @staticmethod
    def reload_maps():
        from progressbar import progressbar  # pip install progressbar2

        print('Reloading svg maps using ', end='')

        # remove all maps
        PathwayMap.wipe_maps()

        type_dict = PathwayMap._get_type_dict()

        # load maps, their names and their annotations
        maps = [file for file in os.listdir(settings.PATHWAY_MAPS) if file.endswith('.svg')]
        for file in progressbar(maps, max_value=len(maps), redirect_stdout=True):
            print(f'Loading {file}')
            PathwayMap.load_map(
                filename=file,
                type_dict=type_dict
            )

    @staticmethod
    def load_map(filename: str, type_dict: dict):
        slug = slugify(filename.rstrip('.svg'))
        path = f'{settings.PATHWAY_MAPS}/{filename}'

        soup = bs4.BeautifulSoup(open(path).read(), 'xml')
        title = soup.svg['title']

        annotations = []
        for shape in soup.select('[data-annotations]'):
            try:
                shape_annotations = json.loads(shape['data-annotations'])
            except Exception as e:
                print(f'Error in map: {filename} - shape: {shape}.')
                raise e
            assert type(shape_annotations) is list, f'Map {filename} contains a shape with an invalid shape: {shape}'
            annotations.extend(shape_annotations)

        anno_objects = {anno_type: set() for anno_type in type_dict.values() if anno_type != 'ignore'}

        for annotation in annotations:
            assert annotation['type'] in type_dict, \
                f'Map {filename} contains an annotation ({annotation}) that has an unknown type {annotation["type"]}. \
                Please add it to type_dictionary.json.'
            anno_type = type_dict[annotation['type']]
            if anno_type == 'ignore':
                continue
            anno_objects[anno_type].add(annotation['name'])

        map = PathwayMap(
            slug=slug,
            title=title,
            filename=filename
        )
        map.save()

        for anno_type, annotations in anno_objects.items():
            if len(annotations) == 0:
                continue
            add_many_annotations(model=map, anno_type=anno_type, annos_to_add=anno_objects[anno_type])

        return soup, annotations

    @staticmethod
    def wipe_maps():
        PathwayMap.objects.all().delete()
