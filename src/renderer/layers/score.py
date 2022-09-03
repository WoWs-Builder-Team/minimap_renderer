from typing import Optional
from ..data import ReplayData
from renderer.render import Renderer
from renderer.base import LayerBase
from renderer.const import COLORS_NORMAL
from PIL import Image, ImageDraw


ALLY_TIMER_POS = (20, 16)
ENEMY_TIMER_POS = (20, 34)


class LayerScoreBase(LayerBase):
    """The class that handles team scores & score timer.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(
        self,
        renderer: Renderer,
        replay_data: Optional[ReplayData] = None,
        green_tag: Optional[str] = None,
        red_tag: Optional[str] = None,
    ):
        self._renderer = renderer
        self._replay_data = (
            replay_data if replay_data else self._renderer.replay_data
        )
        self._green_tag = green_tag
        self._red_tag = red_tag
        self._font = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=28
        )
        self._timers_font = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=17
        )
        self._base = Image.new("RGBA", (714, 50))
        self._timers_base = Image.new("RGBA", (40, 50))
        draw = ImageDraw.Draw(self._timers_base)
        draw.text(
            ALLY_TIMER_POS,
            ":",
            COLORS_NORMAL[0],
            self._timers_font,
            anchor="mm",
        )
        draw.text(
            ENEMY_TIMER_POS,
            ":",
            COLORS_NORMAL[1],
            self._timers_font,
            anchor="mm",
        )

    @staticmethod
    def _ttw_label(time_to_win: float) -> tuple[str, str]:
        """Formats the time.

        Args:
            time_to_win (float): Time to win.

        Returns:
            tuple[str, str]: The formatted time.
        """
        if time_to_win == -1:
            return "--", "--"

        minutes, seconds = int(time_to_win // 60), int(time_to_win % 60)
        return f"{minutes:02d}", f"{seconds:02d}"

    def draw(self, game_time: int, image: Image.Image):
        """Draws the score bar, score text and score timer into the image.

        Args:
            game_time (int): _description_
            image (Image.Image): _description_
        """
        evt_score = self._replay_data.events[game_time].evt_score
        base = self._base.copy()

        sc1 = evt_score[0]
        sc2 = evt_score[1]

        per1 = 1 - sc1.score / self._replay_data.game_win_score
        per2 = 1 - sc2.score / self._replay_data.game_win_score

        draw = ImageDraw.Draw(base)
        st = f"{sc1.score} : {sc2.score}"
        st_w, st_h = self._font.getbbox(st)[2:]
        st_h += 5
        draw.text(
            (
                round(base.width / 2 - st_w / 2),
                round(base.height / 2 - st_h / 2),
            ),
            text=st,
            font=self._font,
            fill="white",
        )

        mid = base.width / 2
        space_width = 150
        margin = 5

        x1, y1 = margin, margin
        x2, y2 = mid - space_width / 2, base.height - margin
        draw.rectangle(((x1, y1), (x2, y2)), outline=COLORS_NORMAL[0])
        x3, y3 = mid + space_width / 2, margin
        x4, y4 = base.width - margin, base.height - margin
        draw.rectangle(((x3, y3), (x4, y4)), outline=COLORS_NORMAL[1])
        a1, b1 = margin, margin
        a2, b2 = mid - space_width / 2, base.height - margin
        a1 = margin + (x2 * per1) - (margin * per1)
        draw.rectangle(((a1, b1), (a2, b2)), fill=COLORS_NORMAL[0])
        a3, b3 = mid + space_width / 2, margin
        a4, b4 = base.width - margin, base.height - margin
        a4 = x4 - (base.width / 2 - space_width / 2) * per2 + (margin * per2)
        draw.rectangle(((a3, b3), (a4, b4)), fill=COLORS_NORMAL[1])

        if self._green_tag:
            self._draw_tag(draw, self._green_tag, (x1, x2), (y1, y2))

        if self._red_tag:
            self._draw_tag(draw, self._red_tag, (x3, x4), (y3, y4))

        image.alpha_composite(base, (40, 0))

        ttw = self._replay_data.events[game_time].evt_times_to_win
        if ttw is None:
            ally_label, enemy_label = ("--", "--"), ("--", "--")
        else:
            ally_label, enemy_label = self._ttw_label(ttw[0]), self._ttw_label(
                ttw[1]
            )
        timers_base = self._timers_base.copy()
        draw = ImageDraw.Draw(timers_base)

        draw.text(
            (ALLY_TIMER_POS[0] - 3, ALLY_TIMER_POS[1]),
            ally_label[0],
            COLORS_NORMAL[0],
            self._timers_font,
            anchor="rm",
        )
        draw.text(
            (ALLY_TIMER_POS[0] + 2, ALLY_TIMER_POS[1]),
            ally_label[1],
            COLORS_NORMAL[0],
            self._timers_font,
            anchor="lm",
        )
        draw.text(
            (ENEMY_TIMER_POS[0] - 3, ENEMY_TIMER_POS[1]),
            enemy_label[0],
            COLORS_NORMAL[1],
            self._timers_font,
            anchor="rm",
        )
        draw.text(
            (ENEMY_TIMER_POS[0] + 2, ENEMY_TIMER_POS[1]),
            enemy_label[1],
            COLORS_NORMAL[1],
            self._timers_font,
            anchor="lm",
        )
        image.alpha_composite(timers_base, (757, 0))

    def _draw_tag(
        self,
        draw: ImageDraw.ImageDraw,
        tag: str,
        bar_xs: tuple,
        bar_ys: tuple,
    ):
        x1, x2 = bar_xs
        y1, y2 = bar_ys
        tw, th = self._font.getsize(tag)
        bar_mid = (x2 - x1) / 2
        bar_mid += x1
        ty = y1 + (y2 - y1) / 2 - th / 2
        ty -= 5
        draw.text(
            (bar_mid - tw / 2, ty),
            tag,
            "white",
            self._font,
            stroke_fill=self._renderer.bg_color,
            stroke_width=2,
        )
