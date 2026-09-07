from renderer.base import LayerBase
from renderer.const import COLORS_NORMAL
from renderer.render import Renderer
from renderer.utils import flip_y
from PIL import Image, ImageDraw
from math import cos, sin, radians, degrees
from typing import Optional, Union
from renderer.data import AcousticTorpedo, ReplayData, Torpedo


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
        self._active_torpedoes: dict[int, Torpedo] = {}
        self._projectiles: dict = self._renderer.resman.load_json(
            "projectiles.json"
        )
        self._relations = {
            v.ship_id: v.relation
            for v in self._replay_data.player_info.values()
        }
        self._hits: set[int] = set()
        self._acoustic_torpedo_buf: dict[int, AcousticTorpedo] = {}

    def draw(
        self,
        game_time: int,
        draw_or_image: Union[ImageDraw.ImageDraw, Image.Image],
    ):
        """This draws the torpedoes to the minimap.

        Args:
            game_time (int): The game time.
            draw_or_image: ImageDraw or Image to draw onto.
        """
        events = self._replay_data.events[game_time]
        self._hits.update(events.evt_hits)

        if not events.evt_torpedo and not self._active_torpedoes:
            return

        draw = (
            draw_or_image
            if isinstance(draw_or_image, ImageDraw.ImageDraw)
            else ImageDraw.Draw(draw_or_image)
        )

        if self._hits and self._active_torpedoes:
            intersection = self._hits.intersection(self._active_torpedoes)
            if intersection:
                for hit in intersection:
                    self._active_torpedoes.pop(hit, None)
                self._hits.difference_update(intersection)

        for sid, torpedo in events.evt_torpedo.items():
            owner_id = torpedo.owner_id
            relation = self._relations.get(torpedo.owner_id, 1)

            x, y = self._renderer.get_scaled(
                (torpedo.origin[0], torpedo.origin[1])
            )
            if relation == 1 and self._renderer.dual_mode:
                continue

            if self._color:
                color = COLORS_NORMAL[0 if self._color == "green" else 1]
            else:
                color = COLORS_NORMAL[relation]

            radius = max(1, self._renderer.px(2))
            draw.ellipse(
                [(x - radius, y - radius), (x + radius, y + radius)],
                fill=color,
            )
        self._active_torpedoes.update(events.evt_torpedo)
        self._acoustic_torpedo_buf.update(events.evt_acoustic_torpedo)

        if self._acoustic_torpedo_buf:
            for sid in list(self._acoustic_torpedo_buf):
                a_torpedo = self._acoustic_torpedo_buf[sid]
                if torpedo := self._active_torpedoes.get(sid):
                    _yaw = round(degrees(a_torpedo.yaw))

                    if _yaw != 360:
                        kwargs = {
                            "origin": (a_torpedo.x, a_torpedo.y),
                            "yaw": a_torpedo.yaw,
                        }
                    else:
                        kwargs = {
                            "origin": (a_torpedo.x, a_torpedo.y),
                        }

                    self._active_torpedoes[sid] = torpedo._replace(**kwargs)
                    del self._acoustic_torpedo_buf[sid]

        for sid, active_torpedo in self._active_torpedoes.items():
            owner_id = active_torpedo.owner_id
            relation = self._relations.get(active_torpedo.owner_id, 1)
            x1, y1 = flip_y(active_torpedo.origin)
            angle = active_torpedo.yaw
            angle = angle - radians(90)
            m_s_bw = active_torpedo.speed_bw * self._renderer.frame_delta
            (x2, y2) = (
                x1 + m_s_bw * cos(angle),
                y1 + m_s_bw * sin(angle),
            )
            x, y = self._renderer.get_scaled((x2, y2), False)

            if relation == 1 and self._renderer.dual_mode:
                continue

            if self._color:
                color = COLORS_NORMAL[0 if self._color == "green" else 1]
            else:
                color = COLORS_NORMAL[relation]

            radius = max(1, self._renderer.px(2))
            draw.ellipse(
                [(x - radius, y - radius), (x + radius, y + radius)],
                fill=color,
            )
            self._active_torpedoes[sid] = active_torpedo._replace(
                origin=(x2, -y2)
            )
