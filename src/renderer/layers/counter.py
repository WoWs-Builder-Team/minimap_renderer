from typing import Optional
from PIL import Image, ImageDraw
from renderer.base import LayerBase
from ..data import ReplayData
from renderer.render import Renderer

COUNTERS = [
    ("Enemy", "DAMAGE", "caused_damage.png", 3, 9),
    ("Agro", "POTENTIAL", "blocked_damage.png", 38, 1),
    ("Spot", "SPOTTING", "assisted_damage.png", 70, 1),
]
COUNTER_COLOR = "#ffffff"

X_POS = 1100
Y_POS = 142


class LayerCounterBase(LayerBase):
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
        self._font_main = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=25
        )
        self._font_com = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=17
        )
        self._y_positions: list[int] = []
        self._counter_numbers: dict[str, list] = {}
        self._counter_name = self.damage_name_icon()

    def damage_name_icon(self):
        """Draws the damage name and icon permanently."""
        assert self._renderer.minimap_bg
        base = Image.new("RGBA", (125, 95))
        draw = ImageDraw.Draw(base)
        space = 12
        y_pos = 0

        for counter in COUNTERS:
            _, name, filename, icon_y, offset_x = counter
            icon = self._renderer.resman.load_image(
                filename, path="counter_icons"
            )
            font = self._font_main if name == "DAMAGE" else self._font_com
            self._y_positions.append(y_pos + Y_POS)
            tw, th = font.getbbox(name)[2:]
            draw.text((0, y_pos), name, COUNTER_COLOR, font)
            base.alpha_composite(icon, (tw + offset_x, icon_y))
            y_pos += th + space
        self._renderer.minimap_bg.alpha_composite(base, (X_POS, Y_POS))

    def draw(self, game_time: int, image: Image.Image):
        """Draws the counters on the minimap image.

        Args:
            game_time (int): Game time. Used to sync. events.
            image (Image.Image): Image where the capture are will be pasted on.
        """
        events = self._replay_data.events
        damage_maps = events[game_time].evt_damage_maps
        y_positions = list(reversed(self._y_positions))

        for counter in COUNTERS:
            (
                name,
                *_,
            ) = counter
            font = self._font_main if name == "Enemy" else self._font_com
            dmg = int(sum(val[1] for val in damage_maps[name].values()))
            y_pos = y_positions.pop()

            if val := self._counter_numbers.get(name, None):
                l_damage, l_image = val
                if l_damage == dmg:
                    x_pos = image.width - l_image.width - 30
                    image.alpha_composite(l_image, (x_pos, y_pos))
                    continue

            value = f"{dmg:,}".replace(",", " ")
            fw, fh = font.getbbox(value)[2:]
            base = Image.new("RGBA", (fw, fh))
            draw = ImageDraw.Draw(base)
            x_pos = image.width - base.width - 30
            draw.text((0, 0), value, COUNTER_COLOR, font)
            self._counter_numbers[name] = [dmg, base.copy()]
            image.alpha_composite(base, (x_pos, y_pos))
