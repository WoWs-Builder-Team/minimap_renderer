from renderer.render import Renderer
from renderer.base import LayerBase
from renderer.const import RELATION_NORMAL_STR, COLORS_NORMAL
from renderer.utils import (
    generate_ship_data,
    paste_centered,
    paste_args_centered,
    draw_health_bar,
)

from PIL import Image, ImageDraw
from math import hypot


class LayerShipBase(LayerBase):
    """A class that handles/draws ships to the minimap.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(self, renderer: Renderer):
        """Initializes this class.

        Args:
            renderer (Renderer): The renderer.
        """
        self._renderer = renderer
        self._ship_info = generate_ship_data(
            self._renderer.replay_data.player_info
        )
        self._active_consumables: dict[int, dict[int, float]] = {}
        self._abilities = renderer.resman.load_json("abilities.json")
        self._ships = renderer.resman.load_json("ships.json")

    def draw(self, game_time: int, image: Image.Image):
        """Draws the ship icons to the minimap image.

        Args:
            game_time (int): The game time.
            image (Image.Image): The minimap image.
        """
        player_info = self._renderer.replay_data.player_info
        events = self._renderer.replay_data.events
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
            holder = self._ship_info[vehicle.avatar_id]
            player = self._renderer.replay_data.player_info[vehicle.avatar_id]
            index, name, species, level = self._ships[player.ship_params_id]

            player = player_info[vehicle.avatar_id]

            icon = self._ship_icon(
                vehicle.is_alive,
                vehicle.is_visible,
                species,
                player.relation,
                vehicle.not_in_range,
            )
            icon = icon.rotate(-vehicle.yaw, Image.BICUBIC, True)
            x, y = self._renderer.get_scaled((vehicle.x, vehicle.y))
            color = (
                COLORS_NORMAL[0]
                if vehicle.relation == -1
                else COLORS_NORMAL[vehicle.relation]
            )

            if vehicle.is_alive:
                if vehicle.is_visible:
                    holder = holder.copy()

                    if vehicle.visibility_flag > 0 and vehicle.relation in [
                        -1,
                        0,
                    ]:
                        vx = 15
                        vy = 65
                        draw = ImageDraw.Draw(holder)
                        draw.rectangle(
                            ((vx, vy), (vx + 5, vy + 5)), fill="orange"
                        )

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

                    d1, d2, d3, d4 = map(
                        lambda ps: round(hypot(x - ps[0], y - ps[1])),
                        side_points,
                    )

                    angle = 0
                    c_y_pos = 20

                    if d1 <= 40 and d2 <= 40:
                        angle = -135
                    elif d2 <= 40 and d3 <= 40:
                        angle = 135
                    elif d3 <= 40 and d4 <= 40:
                        angle = 45
                    elif d4 <= 40 and d1 <= 40:
                        angle = -45
                    else:
                        if d1 <= 40:
                            angle = -90
                        elif d2 <= 40:
                            angle = -180
                        elif d3 <= 40:
                            angle = 90

                    if angle or d4 <= 40:
                        c_y_pos = 83

                    self._ship_consumable(
                        holder,
                        vehicle.vehicle_id,
                        player.ship_params_id,
                        c_y_pos,
                    )

                    if holder:
                        holder = holder.rotate(
                            angle, Image.BICUBIC, expand=True
                        )

                    image.paste(**paste_args_centered(holder, x, y, True))
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
        self, image: Image.Image, vehicle_id: int, params_id: int, y=20
    ):
        """Draws the currently in used consumable(s) to the ship's icon holder.

        Args:
            image (Image.Image): The icon holder.
            vehicle_id (int): The vehicle id.
            params_id (int): The vehicle's game params id.
        """
        if ac := self._active_consumables.get(vehicle_id, {}):
            c_icons_holder = Image.new("RGBA", (20 * len(ac), 20))
            x_pos = 0

            for aid, duration in ac.items():
                cname = self._abilities[params_id][aid]
                filename = f"consumable_{cname}.png"
                c_image = self._renderer.resman.load_image(
                    filename,
                    path="consumables",
                    size=(20, 20),
                )
                c_icons_holder.paste(c_image, (x_pos, 0), c_image)
                x_pos += 20

            image.paste(
                c_icons_holder,
                (int(image.width / 2 - c_icons_holder.width / 2), y),
                c_icons_holder,
            )

    def _ship_icon(
        self,
        is_alive: bool,
        is_visible: bool,
        species: str,
        relation: int,
        not_in_range: bool,
    ) -> Image.Image:
        """Returns an image associated with ship's state.

        Args:
            is_alive (bool): Ship's status.
            is_visible (bool): Ship's visibility.
            species (str): Ship's type.
            relation (int): Ship's relation to player.
            not_in_range (bool): If the ship is in player's render range.

        Returns:
            Image.Image: An icon associated with the ship's state.
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

        return self._renderer.resman.load_image(
            f"{species}.png", path=f"ship_icons.{icon_type}"
        )
