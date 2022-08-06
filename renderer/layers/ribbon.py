from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.render import Renderer

"""
    |  RIBBON_BASE_CAPTURE = 10
     |
     |  RIBBON_BASE_CAPTURE_ASSIST = 11
     |
     |  RIBBON_BASE_DEFENSE = 9
     |
     |  RIBBON_BOMB = 2
     |
     |  RIBBON_BOMB_BULGE = 29
     |
     |  RIBBON_BOMB_NO_PENETRATION = 22
     |
     |  RIBBON_BOMB_OVER_PENETRATION = 20
     |
     |  RIBBON_BOMB_PENETRATION = 21
     |
     |  RIBBON_BOMB_RICOCHET = 23
     |
     |  RIBBON_BUILDING_KILL = 18
     |
     |  RIBBON_BULGE = 28
     |
     |  RIBBON_BURN = 6
     |
     |  RIBBON_CITADEL = 8
     |
     |  RIBBON_CRIT = 4
     |
     |  RIBBON_DETECTED = 19
     |
     |  RIBBON_FLOOD = 7
     |
     |  RIBBON_FRAG = 5
     |
     |  RIBBON_MAIN_CALIBER = 0
     |
     |  RIBBON_MAIN_CALIBER_NO_PENETRATION = 16
     |
     |  RIBBON_MAIN_CALIBER_OVER_PENETRATION = 14
     |
     |  RIBBON_MAIN_CALIBER_PENETRATION = 15
     |
     |  RIBBON_MAIN_CALIBER_RICOCHET = 17
     |
     |  RIBBON_PLANE = 3
     |
     |  RIBBON_ROCKET = 24
     |
     |  RIBBON_ROCKET_BULGE = 30
     |
     |  RIBBON_ROCKET_NO_PENETRATION = 26
     |
     |  RIBBON_ROCKET_OVER_PENETRATION = 35
     |
     |  RIBBON_ROCKET_PENETRATION = 25
     |
     |  RIBBON_ROCKET_RICOCHET = 34
     |
     |  RIBBON_SECONDARY_CALIBER = 13
     |
     |  RIBBON_SPLANE = 27
     |
     |  RIBBON_SUPPRESSED = 12
     |
     |  RIBBON_TORPEDO = 1
"""

SOLO_MAP = {
    1: "torpedo",
    3: "plane",
    4: "crit",
    5: "frag",
    6: "burn",
    7: "flood",
    8: "citadel",
    9: "base_defense",
    10: "base_capture",
    11: "base_capture_assist",
    13: "secondary_caliber",
    18: "building_kill",
    19: "detected",
    31: "dbomb",
    33: "drop",
}


class LayerRibbonBase(LayerBase):
    def __init__(self, renderer: Renderer):
        self._renderer = renderer
        self._font = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=25
        )
        self._images: dict[str, tuple[int, Image.Image]] = {}

    def draw(self, game_time: int, image: Image.Image):
        evt_ribbons = self._renderer.replay_data.events[game_time].evt_ribbon

        if evt_ribbons := evt_ribbons.get(
            self._renderer.replay_data.owner_avatar_id
        ):
            totals = {}

            for r_id, count in evt_ribbons.items():
                name = None
                match r_id:
                    case 0 | 14 | 15 | 16 | 17 | 28:
                        name = "main_caliber"
                    case 24 | 25 | 26 | 30 | 34 | 35:
                        name = "rocket"
                    case 2 | 20 | 21 | 22 | 23 | 29:
                        name = "bomb"
                    case 39 | 40 | 41:
                        name = "acoustic_hit"
                    case _ as solo:
                        name = SOLO_MAP.get(solo, f"unknown_{solo}")
                if name:
                    totals.setdefault(name, 0)
                    totals[name] += count

            x_pos = 805
            y_pos = 145

            for idx, (r_name, r_count) in enumerate(totals.items()):
                r_res = f"{self._renderer.res}.ribbon_icons"
                if "unknown" in r_name:
                    f_name = "ribbon_unknown.png"
                else:
                    f_name = f"ribbon_{r_name}.png"

                if r_name in self._images:
                    c_count, c_image = self._images[r_name]
                    if c_count == r_count:
                        image.paste(c_image, (x_pos, y_pos), c_image)
                        x_pos += c_image.width

                        if (idx + 1) % 4 == 0:
                            y_pos += c_image.height
                            x_pos = 805
                        continue

                r_img = self._renderer.resman.load_image(r_res, f_name)
                r_draw = ImageDraw.Draw(r_img)
                text = f"x{r_count}"
                t_w, t_h = self._font.getsize(text)
                r_draw.text(
                    ((r_img.width - t_w) - 3, (r_img.height - t_h) - 3),
                    text,
                    "white",
                    self._font,
                    stroke_fill="black",
                    stroke_width=1,
                )

                image.paste(r_img, (x_pos, y_pos), r_img)
                x_pos += r_img.width

                if (idx + 1) % 4 == 0:
                    y_pos += r_img.height
                    x_pos = 805

                self._images[r_name] = (r_count, r_img.copy())
