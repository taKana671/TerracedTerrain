from enum import Enum


class Mountain(Enum):

    LAYER_01 = [25, 47, 96, 255]   # iron blue
    LAYER_02 = [38, 73, 157, 255]  # oriental blue
    LAYER_03 = [111, 84, 54, 255]  # burnt umber
    LAYER_04 = [0, 51, 25, 255]
    LAYER_05 = [0, 102, 49, 255]
    LAYER_06 = [0, 133, 54, 255]

    def __init__(self, rgba):
        self.rgba = [round(v / 255, 2) for v in rgba]

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