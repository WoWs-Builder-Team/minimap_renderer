from typing import Optional
from ..base import LayerBase, RendererBase
from ..data import PlayerInfo, Events
from ..utils import (
    generate_ship_data,
    load_image,
    paste_centered,
    paste_args_centered,
    draw_health_bar,
)
from ..const import RELATION_NORMAL_STR, COLORS_NORMAL
from PIL import Image, ImageDraw, ImageFont
from math import hypot


class LayerShip(LayerBase):
    def __init__(self, renderer: RendererBase):
        """A class that handles ship's position, icon.

        Args:
            events (dict[int, Events]): Match events.
            scaling (float): Scaling.
            player_info (dict[int, PlayerInfo]): Player's information.
        """
        self._renderer = renderer
        self._ship_info = generate_ship_data(
            self._renderer.replay_data.player_info
        )

    def generator(self, game_time: int, image: Image.Image):
        """Yields an arguments for Image.paste.

        Args:
            game_time (int): The game's match's time.

        Yields:
            Generator[ dict, None, None ] : A generator.
        """

        player_info = self._renderer.replay_data.player_info
        events = self._renderer.replay_data.events
        scaling = self._renderer.scaling

        for vehicle_id, vehicle in events[game_time].evt_vehicle.items():
            name, species, level, holder = self._ship_info[vehicle.avatar_id]

            player = player_info[vehicle.avatar_id]
            icon = self._ship_icon(
                vehicle.is_alive,
                vehicle.is_visible,
                species,
                player.relation,
                vehicle.not_in_range,
            )
            icon = icon.rotate(-vehicle.yaw, Image.BICUBIC, True)
            x = round(vehicle.x * scaling + 760 / 2)
            y = round(-vehicle.y * scaling + 760 / 2)
            color = (
                COLORS_NORMAL[0]
                if vehicle.relation == -1
                else COLORS_NORMAL[vehicle.relation]
            )

            if vehicle.is_alive:
                if vehicle.is_visible:
                    holder = holder.copy()

                    if not vehicle.not_in_range:
                        draw_health_bar(
                            holder,
                            color=color,
                            hp_per=vehicle.health / player.max_health,
                        )

                    side_points = [
                        (760, y),
                        (x, 760),
                        (0, y),
                        (x, 0),
                    ]

                    rotated_holder = holder

                    d1, d2, d3, d4 = map(
                        lambda ps: round(hypot(x - ps[0], y - ps[1])),
                        side_points,
                    )

                    if d1 <= 40 and d2 <= 40:
                        rotated_holder = holder.rotate(-135, Image.BICUBIC)
                    elif d2 <= 40 and d3 <= 40:
                        rotated_holder = holder.rotate(135, Image.BICUBIC)
                    elif d3 <= 40 and d4 <= 40:
                        rotated_holder = holder.rotate(45, Image.BICUBIC)
                    elif d4 <= 40 and d1 <= 40:
                        rotated_holder = holder.rotate(-45, Image.BICUBIC)
                    else:
                        if d1 <= 40:
                            rotated_holder = holder.rotate(-90, Image.BICUBIC)
                        elif d2 <= 40:
                            rotated_holder = holder.rotate(-180, Image.BICUBIC)
                        elif d3 <= 40:
                            rotated_holder = holder.rotate(90, Image.BICUBIC)

                    icon = paste_centered(rotated_holder, icon)
                    image.paste(**paste_args_centered(icon, x, y, True))
                    image.paste(**paste_args_centered(icon, x, y, True))
                else:
                    image.paste(**paste_args_centered(icon, x, y, True))
            else:
                image.paste(**paste_args_centered(icon, x, y, True))

    def _ship_icon(
        self,
        is_alive: bool,
        is_visible: bool,
        species: str,
        relation: int,
        not_in_range: bool,
    ):
        """Returns an image associated with ship's state.

        Args:
            is_alive (bool): Ship's status.
            is_visible (bool): Ship's visibility.
            species (str): Ship's type.
            relation (int): Ship's relation to player.
            not_in_range (bool): If the ship is in player's render range.

        Returns:
            _type_: An icon associated with the ship's state.
        """
        icon_type = RELATION_NORMAL_STR[relation]

        if relation == -1:
            if is_alive:
                species = "alive"
            else:
                species = "dead"
        else:
            if is_alive:
                if is_visible:
                    if not not_in_range:
                        icon_type = icon_type
                    else:
                        icon_type = f"outside.{icon_type}"
                else:
                    icon_type = "hidden"
            else:
                icon_type = "dead"

        return load_image(
            f"renderer.resources.ship_icons.{icon_type}", f"{species}.png"
        )
