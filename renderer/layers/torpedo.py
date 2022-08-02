import numpy as np

from renderer.base import LayerBase
from renderer.const import COLORS_NORMAL
from renderer.render import Renderer
from renderer.utils import flip_y, getEquidistantPoints
from PIL import ImageDraw
from math import cos, sin, radians, hypot, atan2


class LayerTorpedoBase(LayerBase):
    """Class that handles/draws torpedoes to the minimap.

    Args:
        LayerBase (_type_): _description_
    """
    def __init__(
        self,
        renderer: Renderer,
    ):
        """Initializes this class.

        Args:
            renderer (Renderer): _description_
        """
        self._renderer = renderer
        self._torpedoes: dict[int, list] = {}
        self._projectiles: dict = self._renderer.resman.load_json(
            self._renderer.res, "projectile.json"
        )
        self._relations = {
            v.ship_id: v.relation
            for v in self._renderer.replay_data.player_info.values()
        }
        self._hits: set[int] = set()

    def draw(self, game_time: int, draw: ImageDraw.ImageDraw):
        """This draws the torpedoes to the minimap.

        Args:
            game_time (int): The game time.
            draw (ImageDraw.ImageDraw): Draw.
        """
        events = self._renderer.replay_data.events
        self._hits.update(events[game_time].evt_hits)

        if not events[game_time].evt_torpedo and not self._torpedoes:
            return

        for hit in self._hits.copy():
            if self._torpedoes.pop(hit, None):
                self._hits.remove(hit)

        for torpedo in events[game_time].evt_torpedo:
            x1, y1 = flip_y(torpedo.origin)
            a, b = torpedo.direction

            t_range = self._projectiles[torpedo.params_id][1]
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
            x1, y1 = self._renderer.get_scaled((x1, y1), False)
            x2, y2 = self._renderer.get_scaled((x2, y2), False)
            points = getEquidistantPoints((x1, y1), (x2, y2), t_target)

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
