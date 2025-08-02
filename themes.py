from enum import Enum


class Mountain(Enum):

    LAYER_01 = [25, 47, 96, 255]
    LAYER_02 = [38, 73, 757, 255]
    LAYER_03 = [160, 216, 239, 255]
    LAYER_04 = [255, 247, 153, 255]
    LAYER_05 = [255, 243, 183, 255]
    LAYER_06 = [167, 210, 141, 255]
    LAYER_07 = [97, 142, 52, 255]
    LAYER_08 = [0, 77, 37, 255]
    LAYER_09 = [191, 120, 62, 255]
    LAYER_10 = [143, 101, 82, 255]
    LAYER_11 = [98, 45, 24, 255]
    LAYER_12 = [159, 160, 158, 255]
    LAYER_13 = [78, 69, 74, 255]
    LAYER_14 = [255, 255, 255, 255]

    @classmethod
    def to_dict(cls):
        return {m.name: [round(v / 255, 2) for v in m.value] for m in cls}