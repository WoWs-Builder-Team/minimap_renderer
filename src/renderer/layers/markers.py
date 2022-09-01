from typing import Optional
from ..data import ReplayData
from renderer.render import Renderer
from renderer.base import LayerBase
from renderer.const import RELATION_NORMAL_STR, COLORS_NORMAL
from renderer.utils import (
    generate_ship_data,
    paste_args_centered,
    draw_health_bar,
)

from PIL import Image, ImageDraw
from math import hypot

MIN_VIEW_DISTANCES = {
    1: 15000,
    2: 15000,
    3: 17000,
    4: 20000,
    5: 23000,
    6: 26000,
    7: 27000,
    8: 30000,
    9: 33000,
    10: 35000,
    11: 35000,
}


class LayerShipBase(LayerBase):
    """A class that handles/draws ships to the minimap.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(
        self,
        renderer: Renderer,
        replay_data: Optional[ReplayData] = None,
        color: Optional[str] = None,
    ):
        """Initializes this class.

        Args:
            renderer (Renderer): The renderer.
        """
        self._renderer = renderer
        self._replay_data = (
            replay_data if replay_data else self._renderer.replay_data
        )
        self._color = color
        self._ship_info = generate_ship_data(
            self._replay_data.player_info, renderer.resman, color
        )
        self._active_consumables: dict[int, dict[int, float]] = {}
        self._abilities = renderer.resman.load_json("abilities.json")
        self._ships = renderer.resman.load_json("ships.json")
        self._consumable_cache: dict[int, Image.Image] = {}
        self._owner = self._replay_data.player_info[self._replay_data.owner_id]

    def draw(self, game_time: int, image: Image.Image):
        """Draws the ship icons to the minimap image.

        Args:
            game_time (int): The game time.
            image (Image.Image): The minimap image.
        """
        pass

