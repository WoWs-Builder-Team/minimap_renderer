from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.render import Renderer


COUNTERS = [("Enemy", "DAMAGE", "caused_damage.png", 25, 30, 9, 9),
            ("Agro", "POTENTIAL", "blocked_damage.png", 17, 65, 1, 6),
            ("Spot", "SPOTTING", "assisted_damage.png", 17, 96, 1, 6)]
COUNTER_COLOR = "#ffffff"


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

    def draw(self, game_time: int, image: Image.Image):
        """Draws the counters on the minimap image.

        Args:
            game_time (int): Game time. Used to sync. events.
            image (Image.Image): Image where the capture are will be pasted on.
        """
        draw = ImageDraw.Draw(image)
        events = self._renderer.replay_data.events
        damage_maps = events[game_time].evt_damage_maps

        for name, label, icon_name, font_size, y, gap, anchor_shift in COUNTERS:
            icon = self._renderer.resman.load_image(
                f"{self._renderer.res}.counter_icons", icon_name
            )
            font = self._renderer.resman.load_font(
                filename="warhelios_bold.ttf", size=font_size
            )

            count = int(sum(val[1] for val in damage_maps[name].values()))
            value = f"{count:,}".replace(',', ' ')
            v_w, v_h = font.getsize(value)
            l_w, l_h = font.getsize(label)
            i_w, i_h = icon.width, icon.height

            image.paste(icon, (1110 + l_w + gap, y), icon)
            draw.text(
                (1110, y + i_h / 2 + anchor_shift),
                label,
                fill=COUNTER_COLOR,
                font=font,
                anchor='ls'
            )
            draw.text(
                (1330 - v_w, y + i_h / 2 + anchor_shift),
                value,
                fill=COUNTER_COLOR,
                font=font,
                anchor='ls'
            )

            y += icon.height + 5
