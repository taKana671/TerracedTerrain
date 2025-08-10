from enum import Enum

themes = {}


class Theme(Enum):

    def __init__(self, rgba):
        self.rgba = [round(v / 255, 2) for v in rgba]

    def __init_subclass__(cls):
        super().__init_subclass__()
        themes[cls.__name__.lower()] = cls


class Mountain(Theme):

    LAYER_01 = [25, 47, 96, 255]   # iron blue
    LAYER_02 = [38, 73, 157, 255]  # oriental blue
    LAYER_03 = [111, 84, 54, 255]  # burnt umber
    LAYER_04 = [0, 51, 25, 255]
    LAYER_05 = [0, 102, 49, 255]
    LAYER_06 = [0, 133, 54, 255]

    @classmethod
    def color(cls, z):
        if z <= 0.5:
            return cls.LAYER_01.rgba
        if z <= 0.6:
            return cls.LAYER_02.rgba
        if z <= 0.63:
            return cls.LAYER_03.rgba
        if z <= 0.8:
            return cls.LAYER_04.rgba
        if z <= 1.0:
            return cls.LAYER_05.rgba

        return cls.LAYER_06.rgba


class SnowMountain(Theme):

    LAYER_01 = [3, 51, 102, 255]
    LAYER_02 = [38, 73, 157, 255]
    LAYER_03 = [130, 205, 221, 255]
    LAYER_04 = [125, 125, 125, 255]
    LAYER_05 = [90, 90, 90, 255]
    LAYER_06 = [255, 255, 255, 255]

    @classmethod
    def color(cls, z):
        if z <= 0.3:
            return cls.LAYER_01.rgba
        if z <= 0.5:
            return cls.LAYER_02.rgba
        if z <= 0.6:
            return cls.LAYER_03.rgba
        if z <= 0.8:
            return cls.LAYER_04.rgba
        if z <= 0.9:
            return cls.LAYER_05.rgba

        return cls.LAYER_06.rgba


class Desert(Theme):

    LAYER_01 = [237, 209, 142, 255]
    LAYER_02 = [250, 197, 89, 255]
    LAYER_03 = [153, 96, 49, 255]
    LAYER_04 = [108, 53, 36, 255]
    LAYER_05 = [51, 39, 16, 255]

    @classmethod
    def color(cls, z):
        if z <= 0.5:
            return cls.LAYER_01.rgba
        if z <= 0.58:
            return cls.LAYER_02.rgba
        if z <= 0.85:
            return cls.LAYER_03.rgba
        if z <= 1.1:
            return cls.LAYER_04.rgba

        return cls.LAYER_05.rgba
