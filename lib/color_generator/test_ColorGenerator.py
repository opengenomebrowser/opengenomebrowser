from unittest import TestCase
from .ColorGenerator import ColorGenerator
from collections import Counter


def assert_unique(colors: list) -> bool:
    for color, count in Counter(colors).items():
        assert count == 1, f'Duplicated color: {color=} {count=}'
    return True


SHOW = True
N_COLORS = 5


class TestColorGenerator(TestCase):
    def test_add_colors(self):
        # basic function
        colors = [(1, 1, 1)]
        # add bright
        colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=100, brightness=2)

        print("Your colors:", colors)
        print("In int format:", ColorGenerator.colors_to_int(colors))
        print("In int format:", ColorGenerator.colors_to_hex(colors))
        print("Dark?", [ColorGenerator.is_dark(c, is_float=True) for c in colors])
        self.assertTrue(assert_unique(colors))

        if SHOW:
            ColorGenerator.show_colors(colors)

    def test_import_string(self):
        rgb = ColorGenerator.import_string('3,4,5')
        self.assertEqual(rgb, (3, 4, 5))

    def create_300_unique_hex(self):
        colors = ColorGenerator.get_random_colors(n_colors=300)
        hex = [ColorGenerator.rgb_to_hex(c) for c in colors]
        self.assertTrue(assert_unique(colors))
        self.assertTrue(assert_unique(hex))

        if SHOW:
            ColorGenerator.show_colors(colors)

    def test_red(self):
        colors = ColorGenerator.get_random_colors(n_colors=N_COLORS, b_end=0.2, g_end=0.2)
        if SHOW:
            ColorGenerator.show_colors(colors)

    def test_green(self):
        colors = ColorGenerator.get_random_colors(n_colors=N_COLORS, b_end=0.2, r_end=0.2)
        if SHOW:
            ColorGenerator.show_colors(colors)

    def test_blue(self):
        colors = ColorGenerator.get_random_colors(n_colors=N_COLORS, g_end=0.2, r_end=0.2)
        if SHOW:
            ColorGenerator.show_colors(colors)

    def test_dark(self):
        colors = ColorGenerator.get_random_colors(n_colors=N_COLORS, darkness=2.5)
        if SHOW:
            ColorGenerator.show_colors(colors)

    def test_light(self):
        colors = ColorGenerator.get_random_colors(n_colors=N_COLORS, brightness=2.5)
        if SHOW:
            ColorGenerator.show_colors(colors)

    def test_hex(self):
        colors = [(1, 1, 1), (0.5, 0.5, 0.5), (0, 0, 0)]
        hex = ColorGenerator.colors_to_hex(colors)
        self.assertEqual(hex, ['#ffffff', '#7f7f7f', '#000000'])

    def test_all(self):
        # basic function
        colors = ColorGenerator.get_random_colors(n_colors=N_COLORS)
        colors.append((1, 1, 1))
        # add red
        colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=N_COLORS, b_end=0.2, g_end=0.2)
        colors.append((1, 1, 1))
        # add green
        colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=N_COLORS, b_end=0.2, r_end=0.2)
        colors.append((1, 1, 1))
        # add blue
        colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=N_COLORS, g_end=0.2, r_end=0.2)
        colors.append((1, 1, 1))
        # add dark
        colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=N_COLORS, darkness=2.5)
        colors.append((1, 1, 1))
        # # add bright
        colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=N_COLORS, brightness=2.5)
        colors.append((1, 1, 1))

        print("Your colors:", colors)
        print("In int format:", ColorGenerator.colors_to_int(colors))

        print("Dark?", [ColorGenerator.is_dark(c, is_float=True) for c in colors])

        print(ColorGenerator.import_string('3,4,5'))

        if SHOW:
            ColorGenerator.show_colors(colors)
