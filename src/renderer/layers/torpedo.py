from renderer.base import LayerBase
from renderer.const import COLORS_NORMAL
from renderer.render import Renderer
from renderer.utils import flip_y, getEquidistantPoints
from PIL import ImageDraw
from math import cos, sin, radians, hypot, atan2
from typing import Optional
from renderer.data import ReplayData


class LayerTorpedoBase(LayerBase):
    """Class that handles/draws torpedoes to the minimap.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(
        self,
        renderer: Renderer,
        replay_data: Optional[ReplayData] = None,
        color: Optional[str] = None,
    ):
        """Initializes this class.

        Args:
            renderer (Renderer): _description_
        """
        self._renderer = renderer
        self._replay_data = (
            replay_data if replay_data else self._renderer.replay_data
        )
        self._color = color
        self._torpedoes: dict[int, list] = {}
        self._projectiles: dict = self._renderer.resman.load_json(
            "projectiles.json"
        )
        self._relations = {
            v.ship_id: v.relation
            for v in self._replay_data.player_info.values()
        }
        self._hits: set[int] = set()
        self._fired = []

    def draw(self, game_time: int, draw: ImageDraw.ImageDraw):
        """This draws the torpedoes to the minimap.

        Args:
            game_time (int): The game time.
            draw (ImageDraw.ImageDraw): Draw.
        """
        events = self._replay_data.events
        self._hits.update(events[game_time].evt_hits)

        if events[game_time].evt_acoustic_torpedo:
            for t in events[game_time].evt_acoustic_torpedo.values():
                self._fired.append(int(f"{t.owner_id}{t.shot_id}"))
                x, y = self._renderer.get_scaled((t.x, t.y))

                if (
                    self._relations[t.owner_id] == 1
                    and self._renderer.dual_mode
                ):
                    continue

                if self._color:
                    color = COLORS_NORMAL[0 if self._color == "green" else 1]
                else:
                    color = COLORS_NORMAL[self._relations[t.owner_id]]

                draw.ellipse(
                    [(x - 2, y - 2), (x + 2, y + 2)],
                    fill=color,
                )

        if not events[game_time].evt_torpedo and not self._torpedoes:
            return

        for hit in self._hits.copy():
            if self._torpedoes.pop(hit, None):
                self._hits.remove(hit)

        for torpedo in events[game_time].evt_torpedo:
            if torpedo.shot_id in self._fired:
                continue
            x1, y1 = flip_y(torpedo.origin)
            a, b = torpedo.direction
            igs = 5.219842235292642
            t_range = self._projectiles[torpedo.params_id][1]
            torpedo_range = t_range * 1000
            angle = atan2(a, b)
            angle = angle - radians(90)
            m_s = hypot(a, b) * 30
            m_s = m_s / igs
            t_target = round(torpedo_range / m_s)
            t_target = round(((t_target / 30) * igs) + igs)
            torpedo_range = torpedo_range / 30

            (x2, y2) = (
                x1 + torpedo_range * cos(angle),
                y1 + torpedo_range * sin(angle),
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

                if self._relations[_cid] == 1 and self._renderer.dual_mode:
                    continue

                if self._color:
                    color = COLORS_NORMAL[0 if self._color == "green" else 1]
                else:
                    color = COLORS_NORMAL[self._relations[_cid]]

                draw.ellipse(
                    [(_cx - 2, _cy - 2), (_cx + 2, _cy + 2)],
                    fill=color,
                )
            except IndexError:
                pass
