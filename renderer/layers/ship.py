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
        self._active_consumables: dict[int, dict[int, float]] = {}
        self._abilities = renderer.resman.load_json(
            "renderer.resources", "abilities.json"
        )

    def draw(self, game_time: int, image: Image.Image):
        """Yields an arguments for Image.paste.

        Args:
            game_time (int): The game's match's time.

        Yields:
            Generator[ dict, None, None ] : A generator.
        """

        player_info = self._renderer.replay_data.player_info
        events = self._renderer.replay_data.events
        scaling = self._renderer.scaling
        players_consumables = events[game_time].evt_consumable

        if players_consumables := events[game_time].evt_consumable:
            for player_consumables in players_consumables.values():
                for player_consumable in player_consumables:
                    acs = self._active_consumables.setdefault(
                        player_consumable.ship_id, {}
                    )
                    acs[player_consumable.consumable_id] = round(
                        player_consumable.duration
                    )

        for vehicle in sorted(
            events[game_time].evt_vehicle.values(),
            key=lambda s: (s.is_alive, s.is_visible),
        ):
            name, species, level, holder = self._ship_info[vehicle.avatar_id]

            # if consumables_used := consumables.get(vehicle_id, None):
            #     print(consumables_used)

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

                    self._ship_consumable(
                        holder, vehicle.vehicle_id, player.ship_params_id
                    )

                    if vehicle.visibility_flag > 0 and vehicle.relation in [
                        -1,
                        0,
                    ]:
                        draw = ImageDraw.Draw(holder)
                        draw.ellipse([(27, 38), (30, 42)], fill="orange")

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
                else:
                    image.paste(**paste_args_centered(icon, x, y, True))
            else:
                image.paste(**paste_args_centered(icon, x, y, True))

        # Decrement consumable timer and pop if 0

        for apcs in list(self._active_consumables.keys()):
            for apc in list(self._active_consumables[apcs]):
                if self._active_consumables[apcs][apc] > 0:
                    self._active_consumables[apcs][apc] -= 1
                else:
                    self._active_consumables[apcs].pop(apc)

                    if not self._active_consumables[apcs]:
                        self._active_consumables.pop(apcs)

    def _ship_consumable(
        self, image: Image.Image, vehicle_id: int, params_id: int
    ):
        if ac := self._active_consumables.get(vehicle_id, {}):
            c_icons_holder = Image.new("RGBA", (20 * len(ac), 20))
            x_pos = 0

            for aid, duration in ac.items():
                cname = self._abilities[str(params_id)][str(aid)]
                filename = f"consumable_{cname}.png"
                c_image = self._renderer.resman.load_image(
                    "renderer.resources.consumables", filename, size=(20, 20)
                )
                c_icons_holder.paste(c_image, (x_pos, 0), c_image)
                x_pos += 20

            image.paste(
                c_icons_holder,
                (int(image.width / 2 - c_icons_holder.width / 2), 0),
                c_icons_holder,
            )
            # image.paste(c_image, (x_pos, 10), c_image)
            # x_pos -= 10

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

        # return load_image(
        #     f"renderer.resources.ship_icons.{icon_type}", f"{species}.png"
        # )
        return self._renderer.resman.load_image(
            f"renderer.resources.ship_icons.{icon_type}", f"{species}.png"
        )
