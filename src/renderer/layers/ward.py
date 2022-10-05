from PIL import Image
from renderer.base import LayerBase
from renderer.render import Renderer
from typing import Optional
from renderer.data import ReplayData


RADIUS_MOD = {51: 1.1, 22: 1.1}
SHIP_RADIUS = {
    3751786480: 3.6,  # ENTERPRISE
    3762271696: 3.5,  # CHKALOV
    3764369232: 3.0,  # BÉARN
}
TIER_RADIUS = {
    11: 4.0,
    10: 3.5,
    8: 3.0,
    7: 2.5,
    6: 2.5,
}


class LayerWardBase(LayerBase):
    """A class that handles/draws wards (dropped fighters).

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
            renderer (Renderer): _description_
        """
        self._renderer = renderer
        self._replay_data = (
            replay_data if replay_data else self._renderer.replay_data
        )
        self._vehicle_id_to_player = {
            v.ship_id: v for v in self._replay_data.player_info.values()
        }
        self._color = color
        self._ships = renderer.resman.load_json("ships.json")

    def draw(self, game_time: int, image: Image.Image):
        """Draws the wards to the minimap.

        Args:
            game_time (int): The game time.
            image (Image.Image): The minimap image.

        Returns:
            _type_: _description_
        """

        events = self._replay_data.events
        wards = events[game_time].evt_ward.values()

        if not wards:
            return

        for ward in wards:
            if ward.relation == 1 and self._renderer.dual_mode:
                continue

            player = self._vehicle_id_to_player[ward.vehicle_id]
            ship = self._ships[player.ship_params_id]

            km = SHIP_RADIUS.get(player.ship_params_id, 0.0)
            km = TIER_RADIUS.get(ship["level"], 0.0) if not km else km

            x, y = self._renderer.get_scaled(ward.position)
            m = km * 1000
            bw = m / 30
            r = self._renderer.get_scaled_r(bw)

            try:
                for sid in set(player.skills.AirCarrier).intersection(
                    RADIUS_MOD
                ):
                    r *= RADIUS_MOD[sid]
            except IndexError:
                pass

            w = h = round(r * 2)

            if self._color:
                relation = (
                    "ward_ally" if self._color == "green" else "ward_enemy"
                )
            else:
                relation = (
                    "ward_ally" if ward.relation in [-1, 0] else "ward_enemy"
                )

            filename = relation
            ward_image = self._renderer.resman.load_image(
                f"{filename}.png", size=(w, h)
            )

            image.alpha_composite(
                ward_image,
                (
                    x - round(w / 2),
                    y - round(h / 2),
                ),
            )
