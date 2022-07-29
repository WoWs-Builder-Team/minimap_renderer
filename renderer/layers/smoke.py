from ..base import LayerBase, RendererBase
from typing import Optional
from ..data import Events
from PIL import Image, ImageDraw

import numpy as np


class LayerSmoke(LayerBase):
    def __init__(self, renderer: RendererBase):
        """A class for handling smoke screens.

        Args:
            events (dict[int, Events]): Match events.
            scaling (float): Scaling.
        """
        self._renderer = renderer

    def generator(self, game_time: int, image: Image.Image):
        events = self._renderer.replay_data.events
        smokes = events[game_time].evt_smoke.values()

        if not smokes:
            return None

        assert self._renderer.minimap_image
        base = Image.new("RGBA", self._renderer.minimap_image.size)
        draw = ImageDraw.Draw(base, mode="RGBA")

        for smoke in smokes:
            for point in smoke.points:
                x, y = point
                x = round(self._get_scaled(x))
                y = round(self._get_scaled(-y))
                r = round(smoke.radius * self._renderer.scaling)
                draw.ellipse(
                    [(x - r, y - r), (x + r, y + r)], fill=(255, 255, 255, 64)
                )
        image.paste(base, mask=base)

    def _get_scaled(self, n):
        return n * self._renderer.scaling + 760 / 2
