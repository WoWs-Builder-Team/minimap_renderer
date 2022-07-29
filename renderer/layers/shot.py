import numpy as np

from ..base import LayerBase
from ..data import PlayerInfo, Events
from typing import Optional
from PIL import Image, ImageDraw
from ..const import COLORS_NORMAL


class LayerShot(LayerBase):
    def __init__(
        self,
        events: dict[int, Events],
        scaling: float,
        player_info: dict[int, PlayerInfo],
    ):
        self._events = events
        self._scaling = scaling
        self._projectiles: dict[int, list] = {}
        self._player_relations = {
            v.ship_id: v.relation for v in player_info.values()
        }
        self._empties = 0
        self._hits: set[int] = set()

    def generator(self, game_time: int) -> Optional[Image.Image]:
        if not self._events[game_time].evt_shot and not self._projectiles:
            return None

        base = Image.new("RGBA", (760, 760))
        draw = ImageDraw.Draw(base)
        # self._hits.update(self._events[game_time].evt_hits)

        # for hit in self._hits.copy():
        #     if self._projectiles.pop(hit, None):
        #         self._hits.remove(hit)

        for shot in self._events[game_time].evt_shot:
            result = self.getEquidistantPoints(
                (shot.origin[0], -shot.origin[1]),
                (shot.destination[0], -shot.destination[1]),
                shot.t_time,
            )
            p = self._projectiles.setdefault(shot.shot_id, [])
            prev_x, prev_y = 0, 0

            for (x, y) in result:
                x = int(self._get_scaled(x))
                y = int(self._get_scaled(y))
                p.append(
                    (
                        shot.owner_id,
                        x,
                        y,
                        prev_x if prev_x else x,
                        prev_y if prev_y else y,
                    )
                )
                prev_x, prev_y = x, y

        for sid in list(self._projectiles):
            if projectile := self._projectiles[sid]:
                try:
                    cid, cx, cy, px, py = projectile.pop(0)
                    draw.line(
                        [(cx, cy), (px, py)],
                        fill=COLORS_NORMAL[self._player_relations[cid]],
                        width=2,
                    )
                except IndexError:
                    pass
            else:
                self._projectiles.pop(sid)
        return base

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
