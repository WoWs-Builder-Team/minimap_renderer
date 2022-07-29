from ..base import LayerBase
from typing import Optional
from ..data import Events
from PIL import Image, ImageDraw


class LayerSmoke(LayerBase):
    def __init__(
        self,
        events: dict[int, Events],
        scaling: float,
    ):
        """A class for handling smoke screens.

        Args:
            events (dict[int, Events]): Match events.
            scaling (float): Scaling.
        """
        self._events = events
        self._scaling = scaling

    def generator(self, game_time: int) -> Optional[Image.Image]:
        smokes = self._events[game_time].evt_smoke.values()

        if not smokes:
            return None

        base = Image.new("RGBA", (760, 760))
        draw = ImageDraw.Draw(base)

        for smoke in smokes:
            for point in smoke.points:
                x, y = point
                x = round(x * self._scaling + 760 / 2)
                y = round(-y * self._scaling + 760 / 2)
                r = round(smoke.radius * self._scaling)
                draw.ellipse(
                    [(x - r, y - r), (x + r, y + r)], fill="#ffffff40"
                )

        return base.copy()
