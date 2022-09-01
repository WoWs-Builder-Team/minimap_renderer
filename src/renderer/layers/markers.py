from typing import Optional
from renderer.data import ReplayData
from renderer.render import Renderer
from renderer.base import LayerBase
from renderer.const import RELATION_NORMAL_STR
from PIL import Image, ImageDraw

NAME = {13: "radar", 11: "hydro"}


class LayerMarkersBase(LayerBase):
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
        self._abilities = renderer.resman.load_json("abilities.json")

    def draw(self, game_time: int, image: Image.Image):
        """Draws the ship icons to the minimap image.

        Args:
            game_time (int): The game time.
            image (Image.Image): The minimap image.
        """
        events = self._replay_data.events

        target_ids = set()

        for i in self._renderer.conman.active_consumables.values():
            target_ids.update(i)

        if not target_ids.intersection({11, 13}):
            return

        for vehicle in sorted(
            events[game_time].evt_vehicle.values(),
        ):
            if self._renderer.dual_mode and vehicle.relation == 1:
                continue

            player = self._replay_data.player_info[vehicle.player_id]
            abilities = self._abilities[player.ship_params_id]
            aid_to_subtype = abilities["id_to_subtype"]
            x, y = self._renderer.get_scaled((vehicle.x, vehicle.y))

            if ac := self._renderer.conman.active_consumables.get(
                vehicle.vehicle_id, None
            ):
                if not vehicle.is_visible or not vehicle.is_alive:
                    continue

                if self._color:
                    relation = 0 if self._color == "green" else 1
                else:
                    relation = player.relation

                relation_str = RELATION_NORMAL_STR[relation]

                for aid in {11, 13}.intersection(ac):
                    dist_ship_bw = abilities[aid_to_subtype[aid]]["distShip"]
                    r = round(self._renderer.get_scaled_r(dist_ship_bw) / 2)
                    w = h = r * 2

                    filename = f"{NAME[aid]}_{relation_str}.png"

                    marker = self._renderer.resman.load_image(
                        filename, "markers", size=(w, h)
                    )
                    image.alpha_composite(
                        marker, (x - marker.width // 2, y - marker.height // 2)
                    )
