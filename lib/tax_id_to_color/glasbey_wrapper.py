import os
from math import sqrt


class GlasbeyWrapper:
    @classmethod
    def get_color_from_taxid(cls, taxid: int, scientific_name: str) -> (str, bool):
        """
        :returns color: in rgb-string format, e.g. "255,255,255"
        :returns text_color_white: True if :param color: is dark, False if color is bright

        Picks the color that matches :param taxid: from database/species_color_dict.json if possible.
        Otherwise, it assigns a new color from non_assigned_colors in species_color_dict.json.
        If this is not possible either, new distinct colors are generated using Glasbey.

        :param scientific_name: is only added to species_color_dict.json for human readability
        """
        from website.models import TaxID
        import json
        color_json_path = "database/species_color_dict.json"
        if os.path.isfile(color_json_path):
            with open(color_json_path, 'r') as f:
                color_json = json.load(f)
        else:
            color_json = {"taxid_to_color": {}, "non_assigned_colors": []}

        if str(taxid) in color_json["taxid_to_color"]:
            color = color_json["taxid_to_color"][str(taxid)]["color"]
            return color, GlasbeyWrapper.is_text_color_white(color)

        if len(color_json['non_assigned_colors']) == 0:
            print("loading additional distinct colors for TaxID...")
            used_colors = set()
            # create list of all available colors
            for taxid_entry in color_json["taxid_to_color"]:
                used_colors.add(color_json["taxid_to_color"][taxid_entry]["color"])
            for db_colors in TaxID.objects.values('color').distinct():
                used_colors.add(db_colors["color"])

            used_colors = [cls.__color_str_to_int(color) for color in used_colors]

            # add 30 visually distinct colors to non_assigned_colors
            from .glasbey import Glasbey
            gb = Glasbey(base_palette=used_colors, lightness_range=(80, 100))
            new_colors = gb.convert_palette_to_rgb(gb.generate_palette(len(used_colors) + 30))[-30:]
            new_colors = [str(a) + "," + str(b) + "," + str(c) for a, b, c in new_colors]
            color_json['non_assigned_colors'] = new_colors

        # pick a new color from non_assigned_colors
        color = color_json['non_assigned_colors'].pop()

        color_json["taxid_to_color"][str(taxid)] = {"color": color,
                                                    "scientific_name": scientific_name}

        with open(color_json_path, 'w') as f:
            json.dump(color_json, f)

        return color, GlasbeyWrapper.is_text_color_white(color)

    @classmethod
    def get_color_from_tag(cls, tag: str) -> (str, bool):
        """
        :returns color: in rgb-string format, e.g. "255,255,255"
        :returns text_color_white: True if :param color: is dark, False if color is bright

        Picks the color that matches :param tag: from database/tag_color_dict.json if possible.
        Otherwise, it assigns a new color from non_assigned_colors in tag_color_dict.json.
        If this is not possible either, new distinct colors are generated using Glasbey.
        """
        from website.models import Tag
        import json
        color_json_path = "database/tag_color_dict.json"
        if os.path.isfile(color_json_path):
            with open(color_json_path, 'r') as f:
                color_json = json.load(f)
        else:
            color_json = {"tag_to_color": {}, "non_assigned_colors": []}

        if tag in color_json["tag_to_color"]:
            color = color_json["tag_to_color"][tag]["color"]
            return color, GlasbeyWrapper.is_text_color_white(color)

        if len(color_json['non_assigned_colors']) == 0:
            print("loading additional distinct colors for Tag...")
            used_colors = set()
            # create list of all available colors
            for tag_ in color_json["tag_to_color"]:
                used_colors.add(color_json["tag_to_color"][tag_]["color"])
            for db_colors in Tag.objects.values('color').distinct():
                used_colors.add(db_colors["color"])

            used_colors = [cls.__color_str_to_int(color) for color in used_colors]

            # add 30 visually distinct colors to non_assigned_colors
            from .glasbey import Glasbey
            gb = Glasbey(base_palette=used_colors, chroma_range=(50,100))
            new_colors = gb.convert_palette_to_rgb(gb.generate_palette(len(used_colors) + 30))[-30:]
            new_colors = [str(a) + "," + str(b) + "," + str(c) for a, b, c in new_colors]
            color_json['non_assigned_colors'] = new_colors

        # pick a new color from non_assigned_colors
        color = color_json['non_assigned_colors'].pop()

        color_json["tag_to_color"][tag] = {"color": color}

        with open(color_json_path, 'w') as f:
            json.dump(color_json, f)

        return color, GlasbeyWrapper.is_text_color_white(color)

    @classmethod
    def __color_str_to_int(cls, color: str) -> tuple:
        r, g, b = color.split(",")
        return (int(r), int(g), int(b))

    @staticmethod
    def is_text_color_white(color) -> bool:
        r, g, b = [int(c) for c in color.split(',')]
        luminance = sqrt(0.299 * (r ** 2) + 0.587 * (g ** 2) + 0.114 * (b ** 2))
        return True if luminance < 160 else False
