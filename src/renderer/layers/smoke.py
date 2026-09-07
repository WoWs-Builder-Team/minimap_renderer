from PIL import Image, ImageDraw
from math import ceil, floor
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
        self._cached_smokes = None
        self._cached_sig = None
        self._cached_overlay = None

    def draw(self, game_time: int, image: Image.Image):
        """Draws the smokes to the minimap.

        Args:
            game_time (int): Game time.
            image (Image.Image): Image to paste the smokes to.
        """
        events = self._replay_data.events
        evt_smoke = events[game_time].evt_smoke
        smokes = evt_smoke.values()

        if not smokes:
            return

        smoke_sig = tuple(
            (sid, s.radius, len(s.points)) for sid, s in evt_smoke.items()
        )
        if evt_smoke is self._cached_smokes or smoke_sig == self._cached_sig:
            overlay, position = self._cached_overlay
            image.alpha_composite(overlay, position)
            return

        assert self._renderer.minimap_fg
        circles = []
        for smoke in smokes:
            r = self._renderer.get_scaled_r(smoke.radius)
            for point in smoke.points:
                x, y = self._renderer.get_scaled(point)
                circles.append((x, y, r))

        if not circles:
            return

        left = max(0, floor(min(x - r for x, _, r in circles)))
        top = max(0, floor(min(y - r for _, y, r in circles)))
        right = min(
            image.width, ceil(max(x + r for x, _, r in circles)) + 1
        )
        bottom = min(
            image.height, ceil(max(y + r for _, y, r in circles)) + 1
        )
        if right <= left or bottom <= top:
            return
        base = Image.new("RGBA", (right - left, bottom - top))
        draw = ImageDraw.Draw(base, mode="RGBA")

        for x, y, r in circles:
            draw.ellipse(
                [
                    (x - r - left, y - r - top),
                    (x + r - left, y + r - top),
                ],
                fill="#ffffff40",
            )

        position = (left, top)
        self._cached_smokes = evt_smoke
        self._cached_sig = smoke_sig
        self._cached_overlay = (base, position)
        image.alpha_composite(base, position)
