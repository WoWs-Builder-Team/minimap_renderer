from typing import Optional
from ..data import ReplayData
from renderer.render import Renderer
from renderer.base import LayerBase
from renderer.const import COLORS_NORMAL

from PIL import Image, ImageDraw


class LayerBuildingBase(LayerBase):
    """Class that draws building icons on the minimap.

    Args:
        LayerBase (_type_): Layer base.
    """

    def __init__(
        self,
        renderer: Renderer,
        replay_data: Optional[ReplayData] = None,
    ):
        """Initializes this class.

        Args:
            renderer (Renderer): The renderer.
        """
        self._renderer = renderer
        self._replay_data = (
            replay_data if replay_data else self._renderer.replay_data
        )
        self._buildings: dict = self._renderer.resman.load_json(
            "buildings.json"
        )

    def draw(self, game_time: int, image: Image.Image):
        if not self._replay_data.events[game_time].evt_building:
            return

        for b_id, building in self._replay_data.events[
            game_time
        ].evt_building.items():
            bi = self._replay_data.building_info[b_id]
            species = self._buildings[bi.params_id]

            if species == "Military":
                if building.is_alive:
                    color = COLORS_NORMAL[bi.relation]
                else:
                    color = "#000000"
                icon = Image.new("RGBA", (5, 5))
                icon_draw = ImageDraw.Draw(icon)
                icon_draw.ellipse([(0, 0), icon.size], color)
            else:
                icon = self._get_icon(
                    building.is_alive,
                    building.is_suppressed,
                    bi.relation,
                    species,
                )

            pos = self._renderer.get_scaled((building.x, building.y))
            image.alpha_composite(
                icon,
                (
                    pos[0] - round(icon.width / 2),
                    pos[1] - round(icon.height / 2),
                ),
            )

    def _get_icon(self, is_alive, is_suppressed, relation, species):
        relation_dict = {-1: "neutral", 0: "ally", 1: "enemy"}

        filename_parts = [relation_dict[relation], species]

        if is_alive:
            if is_suppressed:
                filename_parts.append("suppressed")
        else:
            filename_parts = ["dead", species]
        filename = f"{'_'.join(filename_parts)}.png"
        return self._renderer.resman.load_image(filename, "building_icons")
