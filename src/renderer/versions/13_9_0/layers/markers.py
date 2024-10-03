from typing import Optional
from renderer.data import ReplayData
from renderer.render import Renderer
from renderer.base import LayerBase
from renderer.const import COLORS_NORMAL
from PIL import Image, ImageDraw
from functools import lru_cache


class LayerMarkersBase(LayerBase):
    """A class that draws markers to the minimap.

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
        """Draws the markers to the minimap image.

        Args:
            game_time (int): The game time.
            image (Image.Image): The minimap image.
        """
        events = self._replay_data.events

        target_ids = set()

        for i in self._renderer.conman.active_consumables.values():
            target_ids.update(i)

        if not target_ids.intersection({10, 12}):
            return

        for vehicle in sorted(
            events[game_time].evt_vehicle.values(),
        ):
            if self._renderer.dual_mode and vehicle.relation == 1:
                continue

            player = self._replay_data.player_info[vehicle.player_id]
            abilities = self._abilities[player.ship_params_id]
            id_to_subtype = abilities["id_to_subtype"]
            id_to_index = abilities["id_to_index"]
            x, y = self._renderer.get_scaled((vehicle.x, vehicle.y))

            if ac := self._renderer.conman.active_consumables.get(
                vehicle.vehicle_id, None
            ):
                if not vehicle.is_visible or not vehicle.is_alive:
                    continue

                if self._color:
                    color = (
                        COLORS_NORMAL[0]
                        if self._color == "green"
                        else COLORS_NORMAL[1]
                    )
                else:
                    color = COLORS_NORMAL[vehicle.relation]

                for aid in {10, 12}.intersection(ac):
                    name = f"{id_to_index[aid]}.{id_to_subtype[aid]}"
                    dist_ship_bw = abilities[name]["distShip"]
                    r = round(self._renderer.get_scaled_r(dist_ship_bw) / 2)
                    w = h = r * 4

                    if aid == 10:
                        per = dist_ship_bw / 200
                        dash = round(30 * per)
                        shape = self._draw_arc_aa((w, h), color, dash=dash)
                    else:
                        shape = self._draw_ellipse_aa((w, h), color)
                    image.alpha_composite(
                        shape, (x - shape.width // 2, y - shape.height // 2)
                    )

    @lru_cache
    def _draw_arc_aa(
        self,
        size: tuple[int, int],
        color: str = "red",
        aa_level=2,
        width=2,
        dash=60,
    ) -> Image.Image:
        w, h = map(lambda s: s * aa_level, size)
        width *= aa_level
        base = Image.new("RGBA", (w, h))
        draw = ImageDraw.Draw(base)

        d = 360 / dash / 2
        s, e = 0, d
        for _ in range(dash):
            draw.arc(
                [(0, 0), (w - 1, h - 1)],
                fill=color,
                start=s,
                end=e,
                width=width,
            )
            s += d * 2
            e = s + d
        shape_image = base.resize(size, resample=Image.Resampling.LANCZOS)
        return shape_image

    @lru_cache
    def _draw_ellipse_aa(
        self, size: tuple[int, int], color: str = "red", aa_level=2, width=2
    ):

        w, h = map(lambda s: s * aa_level, size)
        width *= aa_level
        base = Image.new("RGBA", (w, h))
        draw = ImageDraw.Draw(base)

        for _ in range(36):
            draw.ellipse([(0, 0), (w - 1, h - 1)], outline=color, width=width)

        shape_image = base.resize(size, resample=Image.Resampling.LANCZOS)
        return shape_image
