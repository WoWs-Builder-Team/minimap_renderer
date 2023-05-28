from typing import Optional
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
        self._empties = 0
        self._hits: set[int] = set()

    def draw(self, game_time: int, image: Image.Image):
        """Draws the shots directly to the image via ImageDraw.

        Args:
            game_time (int): The game time.
            draw (ImageDraw.ImageDraw): Draw.
        """
        events = self._replay_data.events

        if not events[game_time].evt_shot and not self._projectiles:
            return

        base = Image.new("RGBA", image.size)
        draw = ImageDraw.Draw(base)

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
            if projectile := self._projectiles.get(sid, None):
                projectiles.append(projectile.pop(0))
            else:
                self._projectiles.pop(sid)

        projectiles.sort(
            key=lambda o: self._projectiles_data[o[1]], reverse=True
        )

        for projectile in projectiles:
            try:

                cid, params_id, cx, cy, px, py = projectile
                spid, scomp = self._vehicle_components[cid]
                try:
                    atba = self._ships[spid]["components"][scomp["atba"]][
                        "ammo_list"
                    ]
                except KeyError:
                    atba = []
                try:
                    main = self._ships[spid]["components"][scomp["artillery"]][
                        "ammo_list"
                    ]
                except KeyError:
                    main = []
                is_secondary = params_id in atba
                is_secondary = params_id not in main

                if self._renderer.team_tracers:
                    rel = self._relations[cid]
                    if rel == 1 and self._renderer.dual_mode:
                        continue

                    if self._color:
                        color = COLORS_NORMAL[
                            0 if self._color == "green" else 1
                        ]
                    else:
                        color = COLORS_NORMAL[self._relations[cid]]
                else:
                    shell_type = self._projectiles_data[params_id]
                    color = SHELL_COLORS[shell_type]

                if is_secondary:
                    if isinstance(color, str):
                        color = ImageColor.getrgb(color)

                    color = list(color)

                    if len(color) == 3:
                        color.append(85)
                    elif len(color) == 4:
                        color[3] = 85
                    else:
                        raise ValueError("Not a valid color")

                    color = tuple(color)

                draw.line(
                    [(cx, cy), (px, py)],
                    fill=color,
                    width=2,
                )
            except KeyError:
                pass

        image.alpha_composite(base)
