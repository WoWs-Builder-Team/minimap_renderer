from typing import Union

from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.const import (
    COLORS_NORMAL,
    DEATH_TYPES,
    TIER_ROMAN,
)
from renderer.data import Frag
from renderer.render import Renderer
from renderer.utils import do_trim


class LayerChatBase(LayerBase):
    def __init__(self, renderer: Renderer):
        self._renderer = renderer
        self._font = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=12
        )
        self._ships = self._renderer.resman.load_json("ships.json")
        self._players = renderer.replay_data.player_info
        self._generated_lines: dict[int, Image.Image] = {}
        self._messages = []
        self._draw_separator()

    def _draw_separator(self):
        assert self._renderer.minimap_bg
        draw = ImageDraw.Draw(self._renderer.minimap_bg)
        draw.line(((830, 760), (1330, 760)), fill="white", width=5)

    def draw(self, game_time: int, image: Image.Image):
        evt_messages = self._renderer.replay_data.events[game_time].evt_chat
        self._messages.extend(evt_messages)
        # print(len(self._messages))
