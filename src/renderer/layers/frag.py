from typing import Optional, Union

from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.const import (
    COLORS_NORMAL,
    DEATH_TYPES,
    TIER_ROMAN,
)
from renderer.data import Frag, ReplayData
from renderer.render import Renderer


class LayerFragBase(LayerBase):
    """The class for handling frag logs.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(
        self, renderer: Renderer, replay_data: Optional[ReplayData] = None
    ):
        self._renderer = renderer
        self._replay_data = (
            replay_data if replay_data else self._renderer.replay_data
        )
        realm = next(iter(self._replay_data.player_info.values())).realm
        font_name = "warhelios_bold_zh.ttf" if realm == "CN" else "warhelios_bold.ttf"
        self._font = self._renderer.resman.load_font(filename=font_name, size=12)
        self._frags: list[Frag] = []
        self._ships = self._renderer.resman.load_json("ships.json")
        self._players = self._replay_data.player_info
        self._buildings = self._replay_data.building_info
        self._vehicle_id_to_player = {
            v.ship_id: v for k, v in self._players.items()
        }
        self._vehicle_id_to_building = {
            v.id: v for k, v in self._buildings.items()
        }
        self._allies = [
            p.ship_id for p in self._players.values() if p.relation in [-1, 0]
        ]
        self._allies.extend(
            p.id for p in self._buildings.values() if p.relation in [-1, 0]
        )
        self._generated_lines: dict[int, Image.Image] = {}

    def draw(self, game_time: int, image: Image.Image):
        """Draws the frags on the image.

        Args:
            game_time (int): The game time.
            image (Image.Image): The image where the logs will be drawn into.
        """
        evt_flag = self._replay_data.events[game_time].evt_frag
        self._base = Image.new("RGBA", (560, 50))
        self._frags.extend(evt_flag)

        if not self._renderer.enable_chat:
            y_pos = image.height - 5
        else:
            y_pos = 755

        for frag in reversed(self._frags[-5:]):
            is_fragger_building = False
            is_killed_building = False

            try:
                fragger_info = self._vehicle_id_to_player[frag.fragger_id]
            except KeyError:
                fragger_info = self._vehicle_id_to_building[frag.fragger_id]
                is_fragger_building = True

            try:
                killed_info = self._vehicle_id_to_player[frag.killed_id]
            except KeyError:
                killed_info = self._vehicle_id_to_building[frag.killed_id]
                is_killed_building = True

            frag_fname = f"{DEATH_TYPES[frag.death_type]['icon']}.png"
            death_icon = self._renderer.resman.load_image(
                frag_fname, path="frag_icons"
            )

            if self._renderer.anon:
                fr_name = self._renderer.usernames[fragger_info.id]
                kd_name = self._renderer.usernames[killed_info.id]

                if fragger_info.clan_tag:
                    fr_ctag = "#" * len(fragger_info.clan_tag)
                else:
                    fr_ctag = ""

                if killed_info.clan_tag:
                    kd_ctag = "#" * len(killed_info.clan_tag)
                else:
                    kd_ctag = ""

                if fragger_info.relation == -1:
                    fr_name = fragger_info.name

                if killed_info.relation == -1:
                    kd_name = killed_info.name
            else:
                fr_name = fragger_info.name
                kd_name = killed_info.name
                fr_ctag = fragger_info.clan_tag
                kd_ctag = killed_info.clan_tag

            try:
                f_ship = self._ships[fragger_info.ship_params_id]
                f_name = f_ship["name"]
                f_species = f_ship["species"]
                f_level = f_ship["level"]
            except KeyError:
                f_name, f_species, f_level = "", "", 0

            try:
                k_ship = self._ships[killed_info.ship_params_id]
                k_name = k_ship["name"]
                k_species = k_ship["species"]
                k_level = k_ship["level"]
            except KeyError:
                k_name, k_species, k_level = "", "", 0

            line = []

            if is_fragger_building:
                fr_name = "FORT"

            if is_killed_building:
                kd_name = "FORT"

            if frag.fragger_id in self._allies:
                if fr_ctag:
                    line.append((f"[{fr_ctag}]{fr_name}", COLORS_NORMAL[0]))
                else:
                    line.append([fr_name, COLORS_NORMAL[0]])

                line.append(5)

                if not is_fragger_building:
                    line.append(
                        (
                            self._renderer.resman.load_image(
                                f"{f_species}_ally.png",
                                rot=-90,
                                path="ship_icons",
                            ),
                            4,
                            1,
                        )
                    )
                    line.append(5)
                    line.append((TIER_ROMAN[f_level - 1], COLORS_NORMAL[0]))
                    line.append(5)
                    line.append((f_name, COLORS_NORMAL[0]))
                    line.append(5)
                line.append((death_icon, -3, 1))
                line.append("after")
                line.append(5)

                if kd_ctag:
                    line.append((f"[{kd_ctag}]{kd_name}", COLORS_NORMAL[1]))
                else:
                    line.append([kd_name, COLORS_NORMAL[1]])

                line.append(5)
                if not is_killed_building:
                    line.append(
                        (
                            self._renderer.resman.load_image(
                                f"{k_species}_enemy.png",
                                rot=90,
                                path="ship_icons",
                            ),
                            4,
                            1,
                        )
                    )
                    line.append(5)
                    line.append((TIER_ROMAN[k_level - 1], COLORS_NORMAL[1]))
                    line.append(5)
                    line.append((k_name, COLORS_NORMAL[1]))
            else:
                if fr_ctag:
                    line.append((f"[{fr_ctag}]{fr_name}", COLORS_NORMAL[1]))
                else:
                    line.append([fr_name, COLORS_NORMAL[1]])

                line.append(5)

                if not is_fragger_building:
                    line.append(
                        (
                            self._renderer.resman.load_image(
                                f"{f_species}_enemy.png",
                                rot=90,
                                path="ship_icons",
                            ),
                            4,
                            1,
                        )
                    )
                    line.append(5)
                    line.append((TIER_ROMAN[f_level - 1], COLORS_NORMAL[1]))
                    line.append(5)
                    line.append((f_name, COLORS_NORMAL[1]))
                    line.append(5)
                line.append((death_icon, -3, 1))
                line.append("after")
                line.append(5)

                if kd_ctag:
                    line.append((f"[{kd_ctag}]{kd_name}", COLORS_NORMAL[0]))
                else:
                    line.append([kd_name, COLORS_NORMAL[0]])

                line.append(5)

                if not is_killed_building:
                    line.append(
                        (
                            self._renderer.resman.load_image(
                                f"{k_species}_ally.png",
                                rot=-90,
                                path="ship_icons",
                            ),
                            4,
                            1,
                        )
                    )
                    line.append(5)
                    line.append((TIER_ROMAN[k_level - 1], COLORS_NORMAL[0]))
                    line.append(5)
                    line.append((k_name, COLORS_NORMAL[0]))

            for img in self.build(line):
                y_pos -= img.height
                x_pos = (image.width - 30) - img.width
                image.alpha_composite(img, (x_pos, y_pos))

    def _hash(self, line):
        """Hashes the line for caching.

        Args:
            line (_type_): _description_

        Returns:
            _type_: _description_
        """
        hashables = []
        for el in line:
            if isinstance(el, tuple):
                for sel in el:
                    if isinstance(sel, (str, int)):
                        hashables.append(sel)
            elif isinstance(el, int):
                hashables.append(el)
        return hash(tuple(hashables)) & 1000000000

    def build(self, line: list[Union[int, str, Image.Image]]):
        """Builds the line or loads it from the cache.

        Args:
            line (list[Union[int, str, Image.Image]]): The line.

        Returns:
            _type_: The image of the line.
        """

        parts: dict[int, list] = {}
        total_width = 0
        idx = 0

        for el in line:
            part = parts.setdefault(idx, [])
            match el:
                case (a, b) if isinstance(a, str) and isinstance(b, str):
                    str_w, _ = self._font.getbbox(a)[2:]
                    total_width += str_w
                    part.append(el)
                case (a, b, c) if isinstance(a, Image.Image) and isinstance(
                    b, int
                ) and isinstance(c, int):
                    nw, nh = round(a.width * c), round(a.height * c)
                    a = a.resize((nw, nh), Image.Resampling.LANCZOS)
                    total_width += a.width
                    part.append(el)
                case a if isinstance(a, int):
                    total_width += a
                    part.append(el)
                case "after":
                    idx += 1

        is_long = total_width > 525

        part_a = parts[0]
        part_b = parts[1]

        if not is_long:
            part_a.extend(part_b)
            yield self._part_to_image(part_a)
        else:
            for part in [part_b, part_a]:
                yield self._part_to_image(part)
        return

    def _part_to_image(self, part):
        line_hash = self._hash(part)

        if line_hash in self._generated_lines:
            return self._generated_lines[line_hash]

        base = Image.new("RGBA", (525, 17))
        base_draw = ImageDraw.Draw(base)
        pos_x = 0

        for el in part:
            match el:
                case (a, b) if isinstance(a, str) and isinstance(b, str):
                    str_w, _ = self._font.getbbox(a)[2:]
                    base_draw.text((pos_x, 0), a, b, self._font)
                    pos_x += str_w
                case (a, b, c) if isinstance(a, Image.Image) and isinstance(
                    b, int
                ) and isinstance(c, int):
                    nw, nh = round(a.width * c), round(a.height * c)
                    a = a.resize((nw, nh), Image.Resampling.LANCZOS)
                    base.alpha_composite(a, (pos_x, 0 + b))
                    pos_x += a.width
                case a if isinstance(a, int):
                    pos_x += a
        base = base.crop((0, 0, pos_x, 17))
        self._generated_lines[line_hash] = base
        return base
