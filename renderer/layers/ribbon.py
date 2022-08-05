import numpy as np

from typing import Union
from renderer.data import PlayerInfo
from renderer.render import Renderer
from renderer.base import LayerBase
from renderer.const import RELATION_NORMAL_STR, COLORS_NORMAL
from PIL import Image, ImageDraw, ImageColor


"""
    |  RIBBON_BASE_CAPTURE = 10
     |
     |  RIBBON_BASE_CAPTURE_ASSIST = 11
     |
     |  RIBBON_BASE_DEFENSE = 9
     |
     |  RIBBON_BOMB = 2
     |
     |  RIBBON_BOMB_BULGE = 29
     |
     |  RIBBON_BOMB_NO_PENETRATION = 22
     |
     |  RIBBON_BOMB_OVER_PENETRATION = 20
     |
     |  RIBBON_BOMB_PENETRATION = 21
     |
     |  RIBBON_BOMB_RICOCHET = 23
     |
     |  RIBBON_BUILDING_KILL = 18
     |
     |  RIBBON_BULGE = 28
     |
     |  RIBBON_BURN = 6
     |
     |  RIBBON_CITADEL = 8
     |
     |  RIBBON_CRIT = 4
     |
     |  RIBBON_DETECTED = 19
     |
     |  RIBBON_FLOOD = 7
     |
     |  RIBBON_FRAG = 5
     |
     |  RIBBON_MAIN_CALIBER = 0
     |
     |  RIBBON_MAIN_CALIBER_NO_PENETRATION = 16
     |
     |  RIBBON_MAIN_CALIBER_OVER_PENETRATION = 14
     |
     |  RIBBON_MAIN_CALIBER_PENETRATION = 15
     |
     |  RIBBON_MAIN_CALIBER_RICOCHET = 17
     |
     |  RIBBON_PLANE = 3
     |
     |  RIBBON_ROCKET = 24
     |
     |  RIBBON_ROCKET_BULGE = 30
     |
     |  RIBBON_ROCKET_NO_PENETRATION = 26
     |
     |  RIBBON_ROCKET_OVER_PENETRATION = 35
     |
     |  RIBBON_ROCKET_PENETRATION = 25
     |
     |  RIBBON_ROCKET_RICOCHET = 34
     |
     |  RIBBON_SECONDARY_CALIBER = 13
     |
     |  RIBBON_SPLANE = 27
     |
     |  RIBBON_SUPPRESSED = 12
     |
     |  RIBBON_TORPEDO = 1
"""

RIBBON_MAPPING = {
    (14, 15, 16, 17): "main_caliber",
    (24, 25, 26, 30, 34, 35): "rocket"
}


class LayerRibbonBase(LayerBase):
    def __init__(self, renderer: Renderer):
        self._renderer = renderer
        self._font = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=28
        )

    def draw(self, game_time: int, image: Image.Image):
        evt_ribbons = self._renderer.replay_data.events[game_time].evt_ribbon

        if evt_ribbons := evt_ribbons.get(
            self._renderer.replay_data.owner_avatar_id
        ):
            totals = {}
            for r_id, count in evt_ribbons.items():
                name = None
                match r_id:
                    case 14 | 15 | 16 | 17:
                        name = "main_caliber"
                    case 24 | 25 | 26 | 30 | 34 | 35:
                        name = "rocket"
                    case 2 | 20 | 21 | 22 | 23 | 29:
                        name = "bomb"
                    case 3:
                        name = "plane"
                    case 4:
                        name = "crit"
                    case 5:
                        name = "frag"
                    case 6:
                        name = "burn"
                    case 7:
                        name = "flood"
                    case 19:
                        name = "detected"
                    case 1:
                        name = "torpedo"
                if name:
                    totals.setdefault(name, 0)
                    totals[name] += count
            
            print(totals)
