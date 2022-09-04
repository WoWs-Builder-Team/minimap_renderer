from renderer.base import LayerBase
from renderer.const import COLORS_NORMAL
from renderer.render import Renderer
from renderer.utils import flip_y, getEquidistantPoints
from PIL import ImageDraw
from math import cos, sin, radians, hypot, atan2
from typing import Optional
from renderer.data import ReplayData, Torpedo


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
        self._torpedoes: dict[int, list[Torpedo]] = {}
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

        if not events[game_time].evt_torpedo and not self._torpedoes:
            return

        for hit in self._hits.copy():
            try:
                f_torps = self._torpedoes[game_time]
                if _ := f_torps.pop(
                    f_torps.index(
                        [t for t in f_torps if t.shot_id == hit].pop()
                    )
                ):
                    self._hits.remove(hit)
            except Exception:
                pass

        for at in events[game_time].evt_acoustic_torpedo.values():
            try:
                f_torps = self._torpedoes[game_time]
                if matched := f_torps.pop(
                    f_torps.index(
                        [t for t in f_torps if t.shot_id == at.shot_id].pop()
                    )
                ):
                    if at.yaw_speed == 0.0:
                        kwargs = {
                            "origin": (at.x, at.y),
                        }
                    else:
                        kwargs = {"origin": (at.x, at.y), "yaw": at.yaw}
                    f_torps.append(matched._replace(**kwargs))
            except Exception:
                pass

        for torpedo in events[game_time].evt_torpedo:
            x, y = self._renderer.get_scaled(
                (torpedo.origin[0], torpedo.origin[1])
            )
            if (
                self._relations[torpedo.owner_id] == 1
                and self._renderer.dual_mode
            ):
                continue

            if self._color:
                color = COLORS_NORMAL[0 if self._color == "green" else 1]
            else:
                color = COLORS_NORMAL[self._relations[torpedo.owner_id]]

            draw.ellipse(
                [(x - 2, y - 2), (x + 2, y + 2)],
                fill=color,
            )

            p = self._torpedoes.setdefault(game_time + 1, [])
            p.append(torpedo)

        if torpedoes := self._torpedoes.get(game_time):
            for torpedo in torpedoes[:]:
                try:
                    old = torpedoes.pop(torpedoes.index(torpedo))
                except Exception:
                    pass
                else:
                    x1, y1 = flip_y(old.origin)
                    angle = torpedo.yaw
                    angle = angle - radians(90)
                    m_s_bw = torpedo.speed_bw
                    (x2, y2) = (
                        x1 + m_s_bw * cos(angle),
                        y1 + m_s_bw * sin(angle),
                    )
                    x, y = self._renderer.get_scaled((x2, y2), False)

                    if (
                        self._relations[old.owner_id] == 1
                        and self._renderer.dual_mode
                    ):
                        continue

                    if self._color:
                        color = COLORS_NORMAL[
                            0 if self._color == "green" else 1
                        ]
                    else:
                        color = COLORS_NORMAL[self._relations[old.owner_id]]

                    draw.ellipse(
                        [(x - 2, y - 2), (x + 2, y + 2)],
                        fill=color,
                    )
                    t = self._torpedoes.setdefault(game_time + 1, [])
                    t.append(old._replace(origin=(x2, -y2)))
