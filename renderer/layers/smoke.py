from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.render import Renderer


class LayerSmokeBase(LayerBase):
    """The class that handles/draws smokes to the minimap.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(self, renderer: Renderer):
        """Initializes this class.

        Args:
            renderer (Renderer): _description_
        """
        self._renderer = renderer

    def draw(self, game_time: int, image: Image.Image):
        """Draws the smokes to the minimap.

        Args:
            game_time (int): Game time.
            image (Image.Image): Image to paste the smokes to.
        """
        events = self._renderer.replay_data.events
        smokes = events[game_time].evt_smoke.values()

        if not smokes:
            return

        assert self._renderer.minimap_image
        base = Image.new("RGBA", self._renderer.minimap_image.size)
        draw = ImageDraw.Draw(base, mode="RGBA")

        for smoke in smokes:
            for point in smoke.points:
                x, y = self._renderer.get_scaled(point)
                r = round(smoke.radius * self._renderer.scaling)
                draw.ellipse(
                    [(x - r, y - r), (x + r, y + r)], fill="#ffffff40"
                )
        image.paste(base, mask=base)
