from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.render import Renderer
from typing import Optional
from renderer.data import ReplayData


class LayerSmokeBase(LayerBase):
    """The class that handles/draws smokes to the minimap.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(
        self, renderer: Renderer, replay_data: Optional[ReplayData] = None
    ):
        """Initializes this class.

        Args:
            renderer (Renderer): _description_
        """
        self._renderer = renderer
        self._replay_data = (
            replay_data if replay_data else self._renderer.replay_data
        )

    def draw(self, game_time: int, image: Image.Image):
        """Draws the smokes to the minimap.

        Args:
            game_time (int): Game time.
            image (Image.Image): Image to paste the smokes to.
        """
        events = self._replay_data.events
        smokes = events[game_time].evt_smoke.values()

        if not smokes:
            return

        assert self._renderer.minimap_fg
        base = Image.new("RGBA", self._renderer.minimap_fg.size)
        draw = ImageDraw.Draw(base, mode="RGBA")

        for smoke in smokes:
            for point in smoke.points:
                x, y = self._renderer.get_scaled(point)
                r = self._renderer.get_scaled_r(smoke.radius)
                draw.ellipse(
                    [(x - r, y - r), (x + r, y + r)], fill="#ffffff40"
                )

        image.alpha_composite(base)
