from django.db import models
from django.core.validators import RegexValidator
from .Annotation import Annotation
from website.models.Genome import Genome


class KeggMap(models.Model):
    """
    Represents a KEGG map.

    Imported using lib/custom_kegg
    """

    map_id = models.CharField(validators=[
        RegexValidator(regex='^[0-9\.-]{5}$', message='Has to look like this: "12345"', code='nomatch')],
        max_length=5, primary_key=True)

    map_name = models.CharField(max_length=90)

    annotations = models.ManyToManyField(Annotation)

    #
    # from django.db.models import Q
    # AnnotationKEGG.objects.filter(Q(keggmap='00400') & Q(genome='FAM19471'))
    #

    @staticmethod
    def load_maps(reload_data=True, re_render=True):
        # remove all maps
        KeggMap.wipe_maps(re_render=re_render)

        # load maps, their names and their annotations
        from lib.custom_kegg.custom_kegg import CustomKEGG
        ck = CustomKEGG(reload=reload_data)
        map_to_name_dict: dict = ck.map_to_name_dict

        n_maps = len(map_to_name_dict)
        for i, (map_id, map_name) in enumerate(map_to_name_dict.items()):
            map_to_annos: dict = ck.parse_map_html(map_id)

            print(F'Loading map #{map_id}  \t{i}\tin\t{n_maps}')
            # print(F'Loading map #{map_id}  \t{i} in {n_maps}', end="\r", flush=True)

            # connect map to annotations
            kegg_map = KeggMap(map_id=map_id, map_name=map_name)
            kegg_map.save()
            kegg_map._load_content(
                K_set=map_to_annos['K'],
                EC_set=map_to_annos['EC'],
                R_set=map_to_annos['R']
            )

            if re_render:
                # create svg templates
                rendered = ck.render_svg_object(map_id=map_id, kegg_map_dict=map_to_annos, kegg_svg_id='kegg-svg')
                with open('website/static/kegg/svg/{}.svg'.format(map_id), 'w') as out:
                    out.write(rendered)

    def _load_content(self, K_set, EC_set, R_set):
        # link KEGG-map to annotations
        Genome.add_many_annotations(self=self, anno_type='KG', annos_to_add=K_set)
        Genome.add_many_annotations(self=self, anno_type='EC', annos_to_add=EC_set)
        Genome.add_many_annotations(self=self, anno_type='KR', annos_to_add=R_set)

        assert len(K_set) == len(self.annotations.filter(anno_type='KG'))
        assert len(EC_set) == len(self.annotations.filter(anno_type='EC'))
        assert len(R_set) == len(self.annotations.filter(anno_type='KR'))

    @staticmethod
    def wipe_maps(re_render: bool):
        KeggMap.objects.all().delete()
        if re_render:
            import os, shutil
            shutil.rmtree('website/static/kegg/svg')
            os.makedirs('website/static/kegg/svg')
