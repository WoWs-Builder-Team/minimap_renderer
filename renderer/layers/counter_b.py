from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.render import Renderer


COUNTERS = [
    ("Enemy", "DAMAGE", "caused_damage.png", 3, 9),
    ("Agro", "POTENTIAL", "blocked_damage.png", 38, 1),
    ("Spot", "SPOTTING", "assisted_damage.png", 70, 1),
]
COUNTER_COLOR = "#ffffff"
LEFT = 1100
RIGHT = 1330

X_POS = 1100
Y_POS = 27


class LayerCounterBase(LayerBase):
    """A class for handling/drawing counters.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(self, renderer: Renderer):
        """Initiates this class.

        Args:
            renderer (Renderer): The renderer.
        """
        self._renderer = renderer
        self._dict_counts: dict[str, list] = {
            "Enemy": [0, False],
            "Agro": [0, False],
            "Spot": [0, False],
        }

        self._font_main = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=25
        )
        self._font_com = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=17
        )
        self._y_positions: list[int] = []
        self._counter_name = self.damage_name_icon()

    def damage_name_icon(self):
        base = Image.new("RGBA", (125, 95))
        draw = ImageDraw.Draw(base)
        space = 12
        y_pos = 0

        for counter in COUNTERS:
            _, name, filename, icon_y, offset_x = counter
            icon = self._renderer.resman.load_image(
                f"{self._renderer.res}.counter_icons", filename
            )
            font = self._font_main if name == "DAMAGE" else self._font_com
            self._y_positions.append(y_pos + 27)
            tw, th = font.getsize(name)
            draw.text((0, y_pos), name, "#ffffff", font)
            base.paste(icon, (tw + offset_x, icon_y))
            y_pos += th + space
        return base.copy()

    def draw(self, game_time: int, image: Image.Image):
        """Draws the counters on the minimap image.

        Args:
            game_time (int): Game time. Used to sync. events.
            image (Image.Image): Image where the capture are will be pasted on.
        """
        image.paste(self._counter_name, (X_POS, Y_POS), self._counter_name)
        events = self._renderer.replay_data.events
        damage_maps = events[game_time].evt_damage_maps
        y_positions = list(reversed(self._y_positions))

        # c_enemy = int(sum(val[1] for val in damage_maps["Enemy"].values()))
        # c_agro = int(sum(val[1] for val in damage_maps["Agro"].values()))
        # c_spot = int(sum(val[1] for val in damage_maps["Spot"].values()))

        for counter in COUNTERS:
            (
                name,
                *_,
            ) = counter
            font = self._font_main if name == "Enemy" else self._font_com
            dmg = int(sum(val[1] for val in damage_maps[name].values()))
            value = f"{dmg:,}".replace(",", " ")
            fw, fh = font.getsize(value)
            base = Image.new("RGBA", (fw, fh))
            draw = ImageDraw.Draw(base)
            x_pos = image.width - base.width - 30
            draw.text((0, 0), value, "white", font)
            image.paste(base, (x_pos, y_positions.pop()), base)
