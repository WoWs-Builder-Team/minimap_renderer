import numpy as np
import json

from typing import Optional
from ..base import LayerBase
from ..data import PlayerInfo, Events
from PIL import Image, ImageDraw
from ..const import COLORS_NORMAL
from math import cos, sin, radians, hypot, atan2
from importlib.resources import open_text


class LayerTorpedo(LayerBase):
    def __init__(
        self,
        events: dict[int, Events],
        scaling: float,
        player_info: dict[int, PlayerInfo],
    ):
        self._events = events
        self._scaling = scaling
        self._player_info = player_info
        self._torpedoes: dict[int, list] = {}
        self._projectiles: dict = {}
        self._info_b = {
            v.ship_id: v.relation for v in self._player_info.values()
        }
        self._load_projectile_data()
        self._hits: set[int] = set()

    def _load_projectile_data(self):
        with open_text("renderer.resources", "projectile.json") as text_reader:
            self._projectiles = json.load(text_reader)

    def generator(self, game_time: int) -> Optional[Image.Image]:
        self._hits.update(self._events[game_time].evt_hits)

        if not self._events[game_time].evt_torpedo and not self._torpedoes:
            return None

        base = Image.new("RGBA", (760, 760))
        draw = ImageDraw.Draw(base)

        for hit in self._hits.copy():
            if self._torpedoes.pop(hit, None):
                self._hits.remove(hit)

        for torpedo in self._events[game_time].evt_torpedo:
            x1, y1 = torpedo.origin
            a, b = torpedo.direction

            x1, y1 = x1, -y1
            t_range = self._projectiles[str(torpedo.params_id)][1]
            line_length = t_range * 30
            angle = atan2(a, b)
            angle = angle - radians(90)
            c = 0.1740001682033952
            m_s = hypot(a, b) / c
            t_target = round((t_range * 1000 / m_s) * c)

            (x2, y2) = (
                x1 + line_length * cos(angle),
                y1 + line_length * sin(angle),
            )

            x1, y1, x2, y2 = map(self._get_scaled, [x1, y1, x2, y2])
            points = self.getEquidistantPoints((x1, y1), (x2, y2), t_target)

            p = self._torpedoes.setdefault(torpedo.shot_id, [])
            for (px, py) in points:
                p.append((torpedo.owner_id, px, py))

        for timed_shot in self._torpedoes.values():
            try:
                torp = timed_shot.pop(0)
                (
                    _cid,
                    _cx,
                    _cy,
                ) = torp

                draw.ellipse(
                    [(_cx - 2, _cy - 2), (_cx + 2, _cy + 2)],
                    fill=COLORS_NORMAL[self._info_b[_cid]],
                )
            except IndexError:
                pass

        return base.copy()

    def _get_scaled(self, n):
        return n * self._scaling + 760 / 2

    @staticmethod
    def getEquidistantPoints(
        p1: tuple[float, float], p2: tuple[float, float], parts: int
    ):
        return zip(
            np.round(np.linspace(p1[0], p2[0], parts + 1)),
            np.round(np.linspace(p1[1], p2[1], parts + 1)),
        )
