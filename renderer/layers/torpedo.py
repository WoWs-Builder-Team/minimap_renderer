import numpy as np
import json

from typing import Optional
from ..base import LayerBase, RendererBase
from ..data import PlayerInfo, Events
from PIL import Image, ImageDraw
from ..const import COLORS_NORMAL
from math import cos, sin, radians, hypot, atan2
from importlib.resources import open_text


class LayerTorpedo(LayerBase):
    def __init__(
        self,
        renderer: RendererBase,
    ):
        self._renderer = renderer
        self._torpedoes: dict[int, list] = {}
        self._projectiles: dict = {}
        self._relations = {
            v.ship_id: v.relation
            for v in self._renderer.replay_data.player_info.values()
        }
        self._load_projectile_data()
        self._hits: set[int] = set()

    def _load_projectile_data(self):
        with open_text("renderer.resources", "projectile.json") as text_reader:
            self._projectiles = json.load(text_reader)

    def generator(self, game_time: int, image: Image.Image):
        events = self._renderer.replay_data.events
        self._hits.update(events[game_time].evt_hits)

        if not events[game_time].evt_torpedo and not self._torpedoes:
            return

        draw = ImageDraw.Draw(image)

        for hit in self._hits.copy():
            if self._torpedoes.pop(hit, None):
                self._hits.remove(hit)

        for torpedo in events[game_time].evt_torpedo:
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
                    fill=COLORS_NORMAL[self._relations[_cid]],
                )
            except IndexError:
                pass

    def _get_scaled(self, n):
        return n * self._renderer.scaling + 760 / 2

    @staticmethod
    def getEquidistantPoints(
        p1: tuple[float, float], p2: tuple[float, float], parts: int
    ):
        return zip(
            np.round(np.linspace(p1[0], p2[0], parts + 1)),
            np.round(np.linspace(p1[1], p2[1], parts + 1)),
        )
