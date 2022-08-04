import numpy as np

from renderer.base import LayerBase
from renderer.const import COLORS_NORMAL
from renderer.render import Renderer
from renderer.utils import flip_y, getEquidistantPoints

from PIL import ImageDraw


class LayerShotBase(LayerBase):
    """The class that handles/draws artillery shots.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(
        self,
        renderer: Renderer,
    ):
        """Initilizes this class.

        Args:
            renderer (Renderer): The renderer.
        """
        self._renderer = renderer
        self._projectiles: dict[int, list] = {}
        self._relations = {
            v.ship_id: v.relation
            for v in self._renderer.replay_data.player_info.values()
        }
        self._empties = 0
        self._hits: set[int] = set()

    def draw(self, game_time: int, draw: ImageDraw.ImageDraw):
        """Draws the shots directly to the image via ImageDraw.

        Args:
            game_time (int): The game time.
            draw (ImageDraw.ImageDraw): Draw.
        """
        events = self._renderer.replay_data.events

        if not events[game_time].evt_shot and not self._projectiles:
            return

        # self._hits.update(self._events[game_time].evt_hits)

        # for hit in self._hits.copy():
        #     if self._projectiles.pop(hit, None):
        #         self._hits.remove(hit)

        for shot in events[game_time].evt_shot:
            result = getEquidistantPoints(
                flip_y(shot.origin),
                flip_y(shot.destination),
                shot.t_time,
            )
            p = self._projectiles.setdefault(shot.shot_id, [])
            prev_x, prev_y = self._renderer.get_scaled(shot.origin)

            for (x, y) in result:
                x, y = self._renderer.get_scaled((x, y), False)
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
            try:
                if projectile := self._projectiles[sid]:
                    try:
                        cid, cx, cy, px, py = projectile.pop(0)
                        draw.line(
                            [(cx, cy), (px, py)],
                            fill=COLORS_NORMAL[self._relations[cid]],
                            width=2,
                        )
                    except IndexError:
                        pass
                else:
                    self._projectiles.pop(sid)
            except KeyError:
                pass
