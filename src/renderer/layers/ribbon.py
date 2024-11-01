from typing import Optional
from PIL import Image, ImageDraw
from renderer.base import LayerBase
from ..data import ReplayData
from renderer.render import Renderer


# ModsShell.API_v_1_0.constantsGate.Constants
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
    12: "suppressed",
    13: "secondary_caliber",
    18: "building_kill",
    19: "detected",
    27: "splane",
    31: "dbomb",
    33: "drop",
}


class LayerRibbonBase(LayerBase):
    """The class for handling ribbons & achievements.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(
        self, renderer: Renderer, replay_data: Optional[ReplayData] = None
    ):
        self._renderer = renderer
        self._replay_data = (
            replay_data if replay_data else self._renderer.replay_data
        )
        self._font = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=25
        )
        self._images: dict[str, tuple[int, Image.Image]] = {}
        self._achievements = renderer.resman.load_json("achievements.json")

    def draw(self, game_time: int, image: Image.Image):
        """Draws the ribbons/achievements into the image.

        Args:
            game_time (int): The game time.
            image (Image.Image): The image.
        """
        evt_ribbons = self._replay_data.events[game_time].evt_ribbon
        evt_achievement = self._replay_data.events[game_time].evt_achievement

        x_pos = 805
        y_pos = 260
        last_y_height = 0
        ribbon_count = 0

        if evt_ribbons := evt_ribbons.get(self._replay_data.owner_vehicle_id):
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
                    case 43 | 44:
                        name = "dbomb"
                    case 45:
                        name = "dbomb_mine"
                    case _ as solo:
                        name = SOLO_MAP.get(solo, f"unknown_{solo}")
                if name:
                    totals.setdefault(name, 0)
                    totals[name] += count

            ribbon_count = len(totals)

            for idx, (r_name, r_count) in enumerate(totals.items(), 1):
                r_res = "ribbon_icons"
                if "unknown" in r_name:
                    f_name = "ribbon_unknown.png"
                else:
                    f_name = f"ribbon_{r_name}.png"

                if r_name in self._images:
                    c_count, c_image = self._images[r_name]
                    if c_count == r_count:
                        image.alpha_composite(c_image, (x_pos, y_pos))
                        x_pos += c_image.width
                        last_y_height = c_image.height

                        if idx % 4 == 0:
                            y_pos += c_image.height
                            x_pos = 805
                        continue

                r_img = self._renderer.resman.load_image(f_name, path=r_res)
                r_draw = ImageDraw.Draw(r_img)
                text = f"x{r_count}"
                t_w, t_h = self._font.getbbox(text)[2:]
                r_draw.text(
                    ((r_img.width - t_w) - 3, (r_img.height - t_h) - 3),
                    text,
                    "white",
                    self._font,
                    stroke_fill="black",
                    stroke_width=1,
                )

                image.alpha_composite(r_img, (x_pos, y_pos))
                x_pos += r_img.width
                last_y_height = r_img.height

                if idx % 4 == 0:
                    y_pos += r_img.height
                    x_pos = 805

                self._images[r_name] = (r_count, r_img.copy())

        a_x_pos = 805

        if ribbon_count % 4 != 0:
            y_pos += last_y_height

        if achievements := evt_achievement.get(
            self._replay_data.owner_id, None
        ):
            for a_idx, (a_id, a_count) in enumerate(achievements.items(), 1):
                ui_name = self._achievements[a_id]

                if a_id in self._images:
                    a_c_count, a_c_image = self._images[a_id]
                    if a_count == a_c_count:
                        image.alpha_composite(a_c_image, (a_x_pos, y_pos))
                        a_x_pos += a_c_image.width

                        if a_idx % 6 == 0:
                            y_pos += a_c_image.height
                            a_x_pos = 805
                        continue

                a_icon_res = "achievement_icons"
                a_filename = f"icon_achievement_{ui_name}.png"
                a_image = self._renderer.resman.load_image(
                    a_filename, path=a_icon_res
                )

                if a_count > 1:
                    a_image_draw = ImageDraw.Draw(a_image)
                    a_tw, a_th = self._font.getsize(f"x{a_count}")
                    a_image_draw.text(
                        (
                            (a_image.width - a_tw - 3),
                            (a_image.height - a_th - 3),
                        ),
                        f"x{a_count}",
                        "white",
                        self._font,
                        stroke_width=1,
                        stroke_fill="black",
                    )

                image.alpha_composite(a_image, (a_x_pos, y_pos))

                a_x_pos += a_image.width

                if a_idx % 6 == 0:
                    y_pos += a_image.height
                    a_x_pos = 805

                self._images[a_id] = (a_count, a_image.copy())
