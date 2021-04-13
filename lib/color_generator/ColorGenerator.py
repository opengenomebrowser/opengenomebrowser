from random import uniform
from numpy.random import dirichlet
from math import sqrt


class ColorGenerator:
    @staticmethod
    def __get_color_int(
            start: float,
            end: float
    ) -> float:
        assert 0 <= start <= end <= 1, f'Cannot create valid color! {start=}, {end=}'
        return uniform(start, end)

    @classmethod
    def generate_new_color_bright(
            cls,
            brightness: float,
            existing_colors: [tuple[float, float, float]] = None,
            n_iter: int = 100
    ) -> tuple[float, float, float]:
        assert 0 <= brightness
        min_offsets = (dirichlet([1, 1, 1], size=1) * brightness).tolist()[0]
        # sum(min_offsets) ~ brightness
        r, g, b = [min(i, 1) for i in min_offsets]
        return cls.generate_new_color(existing_colors=existing_colors, r_start=r, g_start=b, b_start=g, n_iter=n_iter)

    @classmethod
    def generate_new_color_dark(
            cls,
            darkness: float,
            existing_colors: [tuple[float, float, float]] = None,
            n_iter: int = 100
    ) -> tuple[float, float, float]:
        assert 0 <= darkness
        min_offsets = (dirichlet([1, 1, 1], size=1) * darkness).tolist()[0]
        # sum(min_offsets) ~ brightness
        r, g, b = [max(1 - i, 0) for i in min_offsets]
        return cls.generate_new_color(existing_colors=existing_colors, r_end=r, g_end=b, b_end=g, n_iter=n_iter)

    @classmethod
    def generate_new_color(
            cls,
            existing_colors: [tuple[float, float, float]] = None,
            n_iter: int = 100,
            **kwargs
    ) -> tuple[float, float, float]:
        if existing_colors is None:
            existing_colors = []

        max_distance = None
        best_color = None
        for i in range(0, n_iter):
            color = cls.get_random_color(**kwargs)
            if not existing_colors:
                return color
            best_distance = min([cls.color_distance(color, c) for c in existing_colors])
            if not max_distance or best_distance > max_distance:
                max_distance = best_distance
                best_color = color
        return best_color

    @classmethod
    def get_random_color(
            cls,
            r_start: float = 0, r_end: float = 1,
            g_start: float = 0, g_end: float = 1,
            b_start: float = 0, b_end: float = 1
    ) -> tuple[float, float, float]:
        return tuple(cls.__get_color_int(start, end) for start, end in [(r_start, r_end), (g_start, g_end), (b_start, b_end)])

    @staticmethod
    def color_distance(
            c1: tuple[float, float, float],
            c2: tuple[float, float, float]
    ) -> float:
        return sum([abs(i1 - i2) for i1, i2 in zip(c1, c2)])

    @classmethod
    def get_random_colors(
            cls,
            n_colors: int,
            existing_colors: [tuple[float, float, float]] = None,
            **kwargs
    ) -> [tuple[float, float, float]]:
        if existing_colors is None:
            existing_colors = []

        if 'darkness' in kwargs:
            fn = cls.generate_new_color_dark
        elif 'brightness' in kwargs:
            fn = cls.generate_new_color_bright
        else:
            fn = cls.generate_new_color

        for i in range(n_colors):
            existing_colors.append(fn(existing_colors=existing_colors, **kwargs))

        return existing_colors

    @classmethod
    def color_to_float(cls, color_int: tuple[int, int, int]) -> tuple[float, float, float]:
        return tuple(c / 255 for c in color_int)

    @classmethod
    def colors_to_float(cls, colors_int: [tuple[int, int, int]]) -> [tuple[float, float, float]]:
        return [cls.color_to_float(color) for color in colors_int]

    @classmethod
    def color_to_int(cls, color: tuple[float, float, float]) -> tuple[int, int, int]:
        return tuple(round(c * 255) for c in color)

    @classmethod
    def colors_to_int(cls, colors: [tuple[float, float, float]]) -> [tuple[int, int, int]]:
        return [cls.color_to_int(color) for color in colors]

    @staticmethod
    def colors_to_cmap(colors: [tuple[float, float, float]]):
        from matplotlib.colors import LinearSegmentedColormap
        return LinearSegmentedColormap.from_list('new_map', colors, N=len(colors))

    @classmethod
    def show_colors(cls, colors: [tuple[float, float, float]]):
        import numpy as np
        from matplotlib import colors as mcolors, colorbar
        from matplotlib import pyplot as plt
        fig, ax = plt.subplots(1, 1, figsize=(15, 2))
        bounds = np.linspace(start=0, stop=len(colors), num=len(colors) + 1)
        norm = mcolors.BoundaryNorm(bounds, len(colors))
        cmap = cls.colors_to_cmap(colors)
        cb = colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, spacing='proportional', ticks=None,
                                   boundaries=bounds, format='%1i', orientation=u'horizontal')
        plt.show()

    @staticmethod
    def import_string(color_string: str) -> tuple[int, int, int]:
        color_int = tuple(int(c) for c in color_string.split(','))
        assert len(color_int) == 3, f'Color malformatted: {color_int=}'
        for color in color_int:
            assert 0 <= color <= 255, f'Color malformatted: {color_int=}, {color=}'
        return color_int

    @classmethod
    def is_dark(cls, color_int: tuple[int, int, int], is_float: bool, threshold: int = 160) -> bool:
        if is_float:
            color_int = cls.color_to_int(color_int)
        r, g, b = color_int
        luminance = sqrt(0.299 * (r ** 2) + 0.587 * (g ** 2) + 0.114 * (b ** 2))
        return luminance < threshold


if __name__ == '__main__':
    # basic function
    colors = [(1, 1, 1)]
    # # add bright
    colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=100, brightness=2)

    print("Your colors:", colors)
    print("In int format:", ColorGenerator.colors_to_int(colors))

    print("Dark?", [ColorGenerator.is_dark(c, is_float=True) for c in colors])

    print(ColorGenerator.import_string('3,4,5'))

    ColorGenerator.show_colors(colors)


    exit(0)

    # basic function
    colors = ColorGenerator.get_random_colors(n_colors=n_colors)
    colors.append((1, 1, 1))
    # add red
    colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=n_colors, b_end=0.2, g_end=0.2)
    colors.append((1, 1, 1))
    # add green
    colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=n_colors, b_end=0.2, r_end=0.2)
    colors.append((1, 1, 1))
    # add blue
    colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=n_colors, g_end=0.2, r_end=0.2)
    colors.append((1, 1, 1))
    # add dark
    colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=n_colors, darkness=2.5)
    colors.append((1, 1, 1))
    # # add bright
    colors = ColorGenerator.get_random_colors(existing_colors=colors, n_colors=n_colors, brightness=2.5)
    colors.append((1, 1, 1))

    print("Your colors:", colors)
    print("In int format:", ColorGenerator.colors_to_int(colors))

    print("Dark?", [ColorGenerator.is_dark(c, is_float=True) for c in colors])

    print(ColorGenerator.import_string('3,4,5'))

    ColorGenerator.show_colors(colors)
