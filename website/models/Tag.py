from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.utils import IntegrityError, ProgrammingError
import os


class Tag(models.Model):
    """
    Tags for strains
    """

    tag = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    color = models.CharField(max_length=11)
    text_color_white = models.BooleanField()  # True == white, False == black

    def natural_key(self):
        return self.tag

    @staticmethod
    def get_or_create_tag(tag: str):
        """
        Add Strain or Member to Tag if it already exists, create new one otherwise.

        :param tag: tag-string
        :returns Tag:
        """
        t = Tag.objects.filter(tag=tag)
        if len(t) == 1:
            # get existing Tag
            t = t[0]
        else:
            # create new Tag
            from lib.tax_id_to_color.glasbey_wrapper import GlasbeyWrapper
            color, text_color_white = GlasbeyWrapper.get_color_from_tag(tag=tag)
            t = Tag(
                tag=tag,
                color=color,
                text_color_white=text_color_white
            )
            t.save()

        return t

    def get_html_badge(self):
        return '<span data-tag="{tag}">{tag}</span>'.format(tag=self.tag)

    @staticmethod
    def getTagList() -> [str]:
        try:
            return [tag.tag for tag in Tag.objects.all()]
        except ProgrammingError:
            print("this should only happen during database setup! see website/models/Tag.getTagList()")
            return ""

    @staticmethod
    def create_tag_color_css():
        all_tags = Tag.objects.all()
        with open('website/static/global/css/tag_color.css', 'w') as f:
            for tag in all_tags:
                css = '[data-tag="' + tag.tag + '"] {background-color: rgb(' + tag.color + '); color: '
                if tag.text_color_white:
                    css += 'white}\n'
                else:
                    css += 'black}\n'
                f.write(css)

    def __str__(self):
        return self.tag

    def invariant(self):
        # assert self.strains.count() > 0
        return True
