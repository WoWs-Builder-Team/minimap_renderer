from typing import Optional
from ..data import ReplayData
from renderer.render import Renderer
from renderer.base import LayerBase
from renderer.const import RELATION_NORMAL_STR, COLORS_NORMAL
from renderer.utils import (
    generate_ship_data,
    paste_args_centered,
    draw_health_bar,
)

from PIL import Image, ImageDraw
from math import hypot

MIN_VIEW_DISTANCES = {
    1: 15000,
    2: 15000,
    3: 17000,
    4: 20000,
    5: 23000,
    6: 26000,
    7: 27000,
    8: 30000,
    9: 33000,
    10: 35000,
    11: 35000,
}


class LayerShipBase(LayerBase):
    """A class that handles/draws ships to the minimap.

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
            renderer (Renderer): The renderer.
        """
        self._renderer = renderer
        self._replay_data = (
            replay_data if replay_data else self._renderer.replay_data
        )
        self._color = color
        self._ship_info = generate_ship_data(
            self._replay_data.player_info, renderer.resman, color
        )
        self._active_consumables: dict[int, dict[int, float]] = {}
        self._abilities = renderer.resman.load_json("abilities.json")
        self._ships = renderer.resman.load_json("ships.json")
        self._consumable_cache: dict[int, Image.Image] = {}
        self._owner = self._replay_data.player_info[self._replay_data.owner_id]
        self._owner_view_range = self._get_max_dist()

    def _get_max_dist(self):
        ship = self._ships[self._owner.ship_params_id]
        if ship["species"] in ["AirCarrier", "Submarine"]:
            return -1

        artillery_comp = self._owner.ship_components["artillery"]
        fire_control_comp = self._owner.ship_components["fireControl"]
        ship_comp = ship["components"]
        max_dist = ship_comp[artillery_comp]["maxDist"]
        max_dist_coef = ship_comp[fire_control_comp]["maxDistCoef"]
        max_dist = max_dist * max_dist_coef
        modernizations = self._renderer.resman.load_json("modernizations.json")

        if mods := set(self._owner.modernization).intersection(
            modernizations["mb_range_modifiers"]
        ):
            for mod_id in mods:
                max_dist *= modernizations["modernizations"][mod_id][
                    "GMMaxDist"
                ]
        return max_dist

    def draw(self, game_time: int, image: Image.Image):
        """Draws the ship icons to the minimap image.

        Args:
            game_time (int): The game time.
            image (Image.Image): The minimap image.
        """
        player_info = self._replay_data.player_info
        events = self._replay_data.events
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
        owner_vehicle = events[game_time].evt_vehicle[self._owner.ship_id]

        for vehicle in sorted(
            events[game_time].evt_vehicle.values(),
        ):
            if self._renderer.dual_mode and vehicle.relation == 1:
                continue

            holder = self._ship_info[vehicle.player_id]
            player = self._replay_data.player_info[vehicle.player_id]
            ship = self._ships[player.ship_params_id]

            owner_view_range = self._owner_view_range

            if acs := self._active_consumables.get(
                owner_vehicle.vehicle_id, None
            ):
                if 1 in acs:
                    owner_abilities = self._abilities[
                        self._owner.ship_params_id
                    ]
                    subtype = owner_abilities["id_to_subtype"][1]
                    owner_view_range *= owner_abilities[subtype][
                        "artilleryDistCoeff"
                    ]

            is_in_view_range = False

            if vehicle.is_visible and vehicle != owner_vehicle:
                distance_bw = hypot(
                    vehicle.x - owner_vehicle.x, vehicle.y - owner_vehicle.y
                )
                owner_ship = self._ships[self._owner.ship_params_id]
                owner_view_range *= 1.25
                owner_view_range = max(
                    owner_view_range, MIN_VIEW_DISTANCES[owner_ship["level"]]
                )
                distance_m = distance_bw * 30
                is_in_view_range = owner_view_range >= distance_m

            if self._color:
                relation = 0 if self._color == "green" else 1
                color = COLORS_NORMAL[0 if self._color == "green" else 1]
            else:
                relation = player.relation
                color = (
                    COLORS_NORMAL[0]
                    if vehicle.relation == -1
                    else COLORS_NORMAL[vehicle.relation]
                )

            player = player_info[vehicle.player_id]

            icon = self._ship_icon(
                vehicle.is_alive,
                vehicle.is_visible,
                ship["species"],
                relation,
                is_in_view_range,
            )
            icon = icon.rotate(-vehicle.yaw, Image.Resampling.BICUBIC, True)
            x, y = self._renderer.get_scaled((vehicle.x, vehicle.y))

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

                    if is_in_view_range:
                        draw_health_bar(
                            holder,
                            color=color,
                            hp_per=round(
                                vehicle.health / player.max_health, 2
                            ),
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

                    match (d1, d2, d3, d4):
                        case (d1, d2, d3, d4) if d1 <= 40 and d2 <= 40:
                            angle = -135
                        case (d1, d2, d3, d4) if d2 <= 40 and d3 <= 40:
                            angle = 135
                        case (d1, d2, d3, d4) if d3 <= 40 and d4 <= 40:
                            angle = 45
                        case (d1, d2, d3, d4) if d4 <= 40 and d1 <= 40:
                            angle = -45
                        case (d1, d2, d3, d4) if d1 <= 40:
                            angle = -90
                        case (d1, d2, d3, d4) if d2 <= 40:
                            angle = -180
                        case (d1, d2, d3, d4) if d3 <= 40:
                            angle = 90

                    if angle or d4 <= 40:
                        c_y_pos = 83

                    self._ship_consumable(
                        holder,
                        vehicle.vehicle_id,
                        player.ship_params_id,
                        c_y_pos,
                    )

                    if holder and angle:
                        holder = holder.rotate(
                            angle, Image.Resampling.BICUBIC, expand=True
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
        if ac := self._active_consumables.get(vehicle_id, None):
            aid_hash = hash(tuple(ac)) & 1000000000

            if c_image := self._consumable_cache.get(aid_hash, None):
                image.paste(
                    c_image,
                    (int(image.width / 2 - c_image.width / 2), y),
                    c_image,
                )
            else:
                c_icons_holder = Image.new("RGBA", (20 * len(ac), 20))
                x_pos = 0

                for aid, duration in ac.items():
                    abilities = self._abilities[params_id]
                    index = abilities["id_to_index"][aid]
                    filename = f"consumable_{index}.png"
                    c_image = self._renderer.resman.load_image(
                        filename,
                        path="consumables",
                        size=(20, 20),
                    )
                    c_icons_holder.paste(c_image, (x_pos, 0), c_image)
                    x_pos += 20

                self._consumable_cache[aid_hash] = c_icons_holder

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
        is_in_view_range: bool,
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

        relation_str = RELATION_NORMAL_STR[relation]
        filename_parts: list[str] = []

        if relation == -1:
            if is_alive:
                filename_parts.append("alive")
            else:
                filename_parts.append("dead")
        else:
            filename_parts.append(species)

            match (is_alive, is_visible, is_in_view_range):
                case True, True, False:
                    filename_parts.append(relation_str)
                    filename_parts.append("outside")
                case True, False, _:
                    filename_parts.append("hidden")
                case False, _, _:
                    filename_parts.append("dead")
                case _:
                    filename_parts.append(relation_str)
        filename = "_".join(filename_parts)
        filename = f"{filename}.png"
        return self._renderer.resman.load_image(filename, "ship_icons")

