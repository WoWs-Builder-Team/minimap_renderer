import numpy as np

from typing import Union
from renderer.data import PlayerInfo
from renderer.render import Renderer
from renderer.base import LayerBase
from renderer.const import RELATION_NORMAL_STR, COLORS_NORMAL
from PIL import Image, ImageDraw, ImageColor

RIBBON_MAPPING = {

}


class LayerRibbonBase(LayerBase):
    def __init__(self, renderer: Renderer):
        self._renderer = renderer
        self._font = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=28
        )

    def draw(self, game_time: int, image: Image.Image):
        evt_ribbons = self._renderer.replay_data.events[game_time].evt_ribbon
        print(evt_ribbons)
        # for rid, count in evt_ribbons.items():
        #     print(rid)
        #     match rid:
        #         case 14 | 15 | 16 | 17: print(count)
