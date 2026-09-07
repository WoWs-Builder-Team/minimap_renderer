from typing import Optional
from math import ceil, floor
from renderer.base import LayerBase
from renderer.const import COLORS_NORMAL
from ..data import ReplayData
from renderer.render import Renderer
from renderer.utils import flip_y, getEquidistantPoints

from PIL import ImageDraw, Image, ImageColor


SHELL_COLORS = {
    "HE": (247, 167, 47),
    "AP": (222, 222, 222),
    "CS": (255, 48, 48),
}
SECONDARY_SHELL_COLORS = {k: (*v, 85) for k, v in SHELL_COLORS.items()}
OPAQUE_SHELL_COLORS = {k: (*v, 255) for k, v in SHELL_COLORS.items()}


class LayerShotBase(LayerBase):
    """The class that handles/draws artillery shots.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(
        self,
        renderer: Renderer,
        replay_data: Optional[ReplayData] = None,
        color: Optional[str] = None,
    ):
        """Initilizes this class.

        Args:
            renderer (Renderer): The renderer.
        """
        self._renderer = renderer
        self._replay_data = (
            replay_data if replay_data else self._renderer.replay_data
        )
        self._color = color
        self._projectiles: dict[int, list] = {}
        self._projectiles_data = self._renderer.resman.load_json(
            "projectiles.json"
        )
        self._ships = renderer.resman.load_json("ships.json")
        self._relations = {
            v.ship_id: v.relation
            for v in self._replay_data.player_info.values()
        }
        self._vehicle_components = {
            v.ship_id: (v.ship_params_id, v.ship_components)
            for v in self._replay_data.player_info.values()
        }
        self._main_ammo: dict[int, set[int]] = {}
        for v in self._replay_data.player_info.values():
            spid = v.ship_params_id
            scomp = v.ship_components
            try:
                main_list = self._ships[spid]["components"][scomp["artillery"]][
                    "ammo_list"
                ]
                self._main_ammo[v.ship_id] = set(main_list)
            except KeyError:
                self._main_ammo[v.ship_id] = set()
        self._empties = 0
        self._hits: set[int] = set()
        self._projectile_phase: dict[int, float] = {}

    def draw(self, game_time: int, image: Image.Image):
        """Draws the shots directly to the image via ImageDraw.

        Args:
            game_time (int): The game time.
            draw (ImageDraw.ImageDraw): Draw.
        """
        events = self._replay_data.events

        if not events[game_time].evt_shot and not self._projectiles:
            return

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
                        shot.params_id,
                        x,
                        y,
                        prev_x if prev_x else x,
                        prev_y if prev_y else y,
                    )
                )
                prev_x, prev_y = x, y

        projectiles = []

        for sid in list(self._projectiles):
            path = self._projectiles.get(sid)
            if not path:
                self._projectiles.pop(sid)
                self._projectile_phase.pop(sid, None)
                continue

            phase = self._projectile_phase.get(sid, 0.0)
            current = path[0]
            following = path[1] if len(path) > 1 else current
            projectile = current[:2] + tuple(
                a + (b - a) * phase
                for a, b in zip(current[2:], following[2:])
            )
            projectiles.append(projectile)

            phase += self._renderer.frame_delta
            while phase >= 1 and path:
                path.pop(0)
                phase -= 1
            self._projectile_phase[sid] = phase

        projectiles.sort(
            key=lambda o: self._projectiles_data[o[1]], reverse=True
        )

        if not projectiles:
            return

        line_width = max(1, self._renderer.px(2))
        padding = line_width + 1

        has_secondary = False
        lines = []

        for projectile in projectiles:
            try:
                cid, params_id, cx, cy, px, py = projectile
                is_secondary = params_id not in self._main_ammo.get(cid, ())

                if self._renderer.team_tracers:
                    rel = self._relations[cid]
                    if rel == 1 and self._renderer.dual_mode:
                        continue

                    if self._color:
                        base_c = COLORS_NORMAL[
                            0 if self._color == "green" else 1
                        ]
                    else:
                        base_c = COLORS_NORMAL[self._relations[cid]]

                    if is_secondary:
                        has_secondary = True
                        color = (*base_c[:3], 85)
                    else:
                        color = base_c
                else:
                    shell_type = self._projectiles_data[params_id]
                    if is_secondary:
                        has_secondary = True
                        color = SECONDARY_SHELL_COLORS[shell_type]
                    else:
                        color = OPAQUE_SHELL_COLORS[shell_type]

                lines.append((cx, cy, px, py, color))
            except KeyError:
                pass

        if not lines:
            return

        if not has_secondary:
            draw = ImageDraw.Draw(image)
            for cx, cy, px, py, color in lines:
                draw.line(
                    [(cx, cy), (px, py)],
                    fill=color,
                    width=line_width,
                )
            return

        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")
        for cx, cy, px, py, _ in lines:
            if cx < min_x: min_x = cx
            if px < min_x: min_x = px
            if cx > max_x: max_x = cx
            if px > max_x: max_x = px
            if cy < min_y: min_y = cy
            if py < min_y: min_y = py
            if cy > max_y: max_y = cy
            if py > max_y: max_y = py

        left = max(0, floor(min_x) - padding)
        top = max(0, floor(min_y) - padding)
        right = min(image.width, ceil(max_x) + padding + 1)
        bottom = min(image.height, ceil(max_y) + padding + 1)

        if right <= left or bottom <= top:
            return

        base = Image.new("RGBA", (right - left, bottom - top))
        draw = ImageDraw.Draw(base)
        for cx, cy, px, py, color in lines:
            draw.line(
                [(cx - left, cy - top), (px - left, py - top)],
                fill=color,
                width=line_width,
            )
        image.alpha_composite(base, (left, top))
