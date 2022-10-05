from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.render import Renderer
from renderer.data import ReplayData
from typing import Optional

FONT_SIZE = 26
NORMAL_COLOR = "#ffffff"
WARNING_COLOR = "#faaf0a"


class LayerTimerBase(LayerBase):
    """A class for handling/drawing counters.

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
        self._font = renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=FONT_SIZE
        )

    def draw(self, game_time: int, image: Image.Image):
        draw = ImageDraw.Draw(image)
        event = self._replay_data.events[game_time]
        time_left = event.time_left
        minutes, seconds = time_left // 60, time_left % 60
        color = WARNING_COLOR if minutes <= 2 else NORMAL_COLOR

        draw.text(
            (10, -5),
            f"{minutes:02d}",
            fill=color,
            font=self._font,
        )
        draw.text(
            (10, 17),
            f"{seconds:02d}",
            fill=color,
            font=self._font,
        )
