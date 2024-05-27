from typing import Optional
from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.render import Renderer
from renderer.const import COLORS_NORMAL, RELATION_NORMAL_STR
from renderer.utils import replace_color
from renderer.data import ReplayData
from functools import lru_cache


class LayerCapture(LayerBase):
    """A class for handling/drawing capture points.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(
        self, renderer: Renderer, replay_data: Optional[ReplayData] = None
    ):
        """Initiates this class.

        Args:
            renderer (Renderer): The renderer.
        """
        self._renderer = renderer
        self._replay_data = (
            replay_data if replay_data else self._renderer.replay_data
        )
        self._owner = self._replay_data.player_info[self._replay_data.owner_id]
        self._generated_caps: dict[
            int, tuple[Image.Image, tuple[int, int], int]
        ] = {}

    def draw(self, game_time: int, image: Image.Image):
        """Draws the capture area on the minimap image.

        Args:
            game_time (int): Game time. Used to sync. events.
            image (Image.Image): Image where the capture are will be pasted on.
        """
        events = self._replay_data.events
        cps = events[game_time].evt_control.values()

        for count, cp in enumerate(cps):
            if not cp.is_visible:
                continue

            if count in self._generated_caps:
                cap_image, cap_pos, cap_hash = self._generated_caps[count]
                if hash(cp) == cap_hash:
                    image.alpha_composite(cap_image, cap_pos)
                    continue

            x, y = self._renderer.get_scaled(cp.position)
            radius = self._renderer.get_scaled_r(cp.radius)
            w = h = round(radius * 2)
            cp_area = self._get_capture_area(cp.relation, (w, h))

            if cp.control_point_type == 5:
                icon_name = "flag.png"
            else:
                icon_name = f"lettered_{count}.png"

            relation_str = RELATION_NORMAL_STR[cp.relation]
            icon = self._renderer.resman.load_image(
                icon_name, path=f"cap_icons.{relation_str}"
            )

            if cp.has_invaders and cp.invader_team != -1:
                if cp.invader_team == self._owner.team_id:
                    from_color = COLORS_NORMAL[cp.relation]
                    to_color = COLORS_NORMAL[0]
                else:
                    from_color = COLORS_NORMAL[cp.relation]
                    to_color = COLORS_NORMAL[1]
                progress = self._get_progress(
                    from_color, to_color, cp.progress
                )
            else:
                normal = self._renderer.resman.load_image("cap_normal.png")
                from_color = "#000000"
                to_color = COLORS_NORMAL[cp.relation]
                progress = replace_color(normal, from_color, to_color)

            px = round(cp_area.width / 2 - progress.width / 2) + 1
            py = round(cp_area.height / 2 - progress.height / 2) + 1

            cp_area.alpha_composite(progress, (px, py))

            ix = round(cp_area.width / 2 - icon.width / 2) + 1
            iy = round(cp_area.height / 2 - icon.height / 2) + 1

            cp_area.alpha_composite(icon, (ix, iy))

            cx = round(x - cp_area.width / 2)
            cy = round(y - cp_area.height / 2)

            self._generated_caps[count] = (
                cp_area.copy(),
                (cx, cy),
                hash(cp)
            )

            image.alpha_composite(cp_area, (cx, cy))

    def _get_capture_area(self, relation: int, size: tuple) -> Image.Image:
        """Loads the proper capture area image from the resources.

        Args:
            relation (int): relation
            size (tuple): size of the image.

        Returns:
            Image.Image: Image of the capture area, resized.
        """
        relation_to_str = {-1: "neutral", 0: "ally", 1: "enemy"}
        filename = f"cap_{relation_to_str[relation]}.png"
        return self._renderer.resman.load_image(filename, size=size)

    @lru_cache
    def _get_progress(self, from_color: str, to_color: str, percent: float):
        """Gets the diamond progress `bar` from the resources and properly
        color it depending from the colors and percentage provided.

        Args:
            from_color (str): From color.
            to_color (str): To color.
            percent (float): Percentage of the progress. 0.0 to 1.0

        Returns:
            Image.Image: Diamond progress `bar` image.
        """
        pd = self._renderer.resman.load_image("cap_invaded.png")

        bg_diamond = replace_color(pd, "#000000", from_color)
        fg_diamond = replace_color(pd, "#000000", to_color)
        mask = Image.new("RGBA", pd.size)
        mask_draw = ImageDraw.Draw(mask, "RGBA")
        mask_draw.pieslice(
            (
                (0, 0),
                (pd.width - 1, pd.height - 1),
            ),
            start=-90,
            end=(-90 + 360 * percent),
            fill="black",
        )
        bg_diamond.paste(fg_diamond, mask=mask)
        return bg_diamond
