from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.render import Renderer
from renderer.const import COLORS_NORMAL
from renderer.utils import replace_color


class LayerCaptureBase(LayerBase):
    """A class for handling/drawing capture points.

    Args:
        LayerBase (_type_): _description_
    """
    def __init__(self, renderer: Renderer):
        """Initiates this class.

        Args:
            renderer (Renderer): The renderer.
        """
        self._renderer = renderer
        self._owner = [
            p
            for p in self._renderer.replay_data.player_info.values()
            if p.relation == -1
        ].pop()

    def draw(self, game_time: int, image: Image.Image):
        """Draws the capture area on the minimap image.

        Args:
            game_time (int): Game time. Used to sync. events.
            image (Image.Image): Image where the capture are will be pasted on.
        """
        events = self._renderer.replay_data.events
        cps = events[game_time].evt_control.values()

        for cp in cps:
            if not cp.is_visible:
                continue
            x, y = self._renderer.get_scaled(cp.position)
            radius = self._renderer.get_scaled_r(cp.radius)
            w = h = round(radius * 2)
            cp_area = self._get_capture_area(cp.relation, (w, h))

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
                normal = self._renderer.resman.load_image(
                    self._renderer.res, "cap_normal.png"
                )
                from_color = "#000000"
                to_color = COLORS_NORMAL[cp.relation]
                progress = replace_color(normal, from_color, to_color)

            progress = progress.resize(
                (round(w / 3), round(h / 3)), resample=Image.BICUBIC
            )

            px = round(cp_area.width / 2 - progress.width / 2)
            py = round(cp_area.height / 2 - progress.height / 2)

            cp_area.paste(progress, (px, py), progress)

            cx = round(x - cp_area.width / 2)
            cy = round(y - cp_area.height / 2)

            image.paste(cp_area, (cx, cy), cp_area)

    def _get_capture_area(self, relation: int, size: tuple) -> Image.Image:
        """Loads the proper capture area image from the resources.

        Args:
            relation (int): relation
            size (tuple): size of the image.

        Returns:
            Image.Image: Image of the capture area, resized.
        """
        package = self._renderer.res
        relation_to_str = {-1: "neutral", 0: "ally", 1: "enemy"}
        filename = f"cap_{relation_to_str[relation]}.png"
        return self._renderer.resman.load_image(package, filename, size=size)

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
        pd = self._renderer.resman.load_image(
            self._renderer.res, "cap_invaded.png"
        )

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
