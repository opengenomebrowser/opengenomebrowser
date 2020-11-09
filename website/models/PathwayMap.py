import os
import json
import bs4
from django.utils.text import slugify
from django.db import models
from .Annotation import Annotation
from website.models.GenomeContent import GenomeContent
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

    @property
    def svg(self):
        return open(F'{settings.PATHWAY_MAPS}/{self.filename}').read()

    @staticmethod
    def _get_type_dict():
        if settings.PATHWAY_MAPS_TYPE_DICT:
            return json.load(open(settings.PATHWAY_MAPS_TYPE_DICT))
        else:
            print('default type dict')
            type_dict = {a.label: a.value for a in Annotation.AnnotationTypes}
            additional = {
                "KEGG Compound": "ignore",
                "KEGG Glycan": "ignore",
                "KEGG Drug": "ignore",
                "KEGG Drug Group": "ignore",
                "KEGG Map": "ignore",
                "Unknown": "ignore"
            }
            type_dict.update(additional)
            return type_dict

    @staticmethod
    def reload_maps():
        from progressbar import progressbar  # pip install progressbar2

        print('Reloading svg maps using ', end='')

        PathwayMap.__ensure_link()
        # remove all maps
        PathwayMap.wipe_maps()

        type_dict = PathwayMap._get_type_dict()

        # load maps, their names and their annotations
        maps = [file for file in os.listdir(settings.PATHWAY_MAPS) if file.endswith('.svg')]
        for file in progressbar(maps, max_value=len(maps), redirect_stdout=True):
            print(F'Loading {file}')
            PathwayMap.load_map(
                filename=file,
                type_dict=type_dict
            )

    @staticmethod
    def load_map(filename: str, type_dict: dict):
        slug = slugify(filename[:-4])
        path = F'{settings.PATHWAY_MAPS}/{filename}'

        soup = bs4.BeautifulSoup(open(path).read(), 'xml')
        title = soup.svg['title']

        annotations = []
        for shape in soup.select('[data-annotations]'):
            annotations.extend(json.loads(shape['data-annotations']))

        anno_objects = {anno_type: set() for anno_type in type_dict.values() if anno_type != 'ignore'}

        for annotation in annotations:
            assert annotation['type'] in type_dict, \
                F'Map {filename} contains an annotation ({annotation}) that has an unknown type {annotation["type"]}. \
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
            GenomeContent.add_many_annotations(model=map, anno_type=anno_type, annos_to_add=anno_objects[anno_type])

        return soup, annotations

    @staticmethod
    def wipe_maps():
        PathwayMap.objects.all().delete()
        PathwayMap.__ensure_link()

    @staticmethod
    def __ensure_link():
        """
        Link static/pathway-maps/svg to settings.PATHWAY_MAPS

        :return: path to settings.PATHWAY_MAPS
        """
        real_dir = settings.PATHWAY_MAPS
        link_dir = F'{settings.BASE_DIR}/website/static/pathway-maps/svg'
        # ensure real_dir exists
        os.makedirs(real_dir, exist_ok=True)
        # ensure link to real_dir exists
        if not os.path.islink(link_dir):
            # ensure parent exists
            os.makedirs(os.path.dirname(link_dir), exist_ok=True)
            os.symlink(real_dir, link_dir)
        return real_dir
