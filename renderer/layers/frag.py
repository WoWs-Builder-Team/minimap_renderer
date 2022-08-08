from typing import Union

from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.const import (
    COLORS_NORMAL,
    DEATH_TYPES,
    TIER_ROMAN,
)
from renderer.data import Frag
from renderer.render import Renderer
from renderer.utils import do_trim


class LayerFragBase(LayerBase):
    """The class for handling frag logs.

    Args:
        LayerBase (_type_): _description_
    """
    def __init__(self, renderer: Renderer):
        self._renderer = renderer
        self._font = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=12
        )
        self._frags: list[Frag] = []
        self._ships = self._renderer.resman.load_json("ships.json")
        self._players = renderer.replay_data.player_info
        self._vehicle_id_to_player = {
            v.ship_id: v for k, v in self._players.items()
        }
        self._allies = [
            p.ship_id for p in self._players.values() if p.relation in [-1, 0]
        ]
        self._generated_lines: dict[int, Image.Image] = {}

    def draw(self, game_time: int, image: Image.Image):
        """Draws the frags on the image.

        Args:
            game_time (int): The game time.
            image (Image.Image): The image where the logs will be drawn into.
        """
        evt_flag = self._renderer.replay_data.events[game_time].evt_frag
        self._base = Image.new("RGBA", (560, 50))
        self._frags.extend(evt_flag)

        y_pos = image.height - 5

        for frag in reversed(self._frags[-5:]):
            fragger_info = self._vehicle_id_to_player[frag.fragger_id]
            killed_info = self._vehicle_id_to_player[frag.killed_id]
            frag_fname = f"{DEATH_TYPES[frag.death_type]['icon']}.png"
            death_icon = self._renderer.resman.load_image(
                frag_fname, path="frag_icons"
            )

            _, f_name, f_species, f_level, _ = self._ships[
                fragger_info.ship_params_id
            ]
            _, k_name, k_species, k_level, _ = self._ships[
                killed_info.ship_params_id
            ]
            icon_res = "ship_icons"
            line = []

            if frag.fragger_id in self._allies:
                ally_icon = self._renderer.resman.load_image(
                    f"{f_species}.png", rot=-90, path=f"{icon_res}.ally"
                )
                enemy_icon = self._renderer.resman.load_image(
                    f"{k_species}.png", rot=90, path=f"{icon_res}.enemy"
                )

                if fragger_info.clan_tag:
                    cn = [
                        (f"[{fragger_info.clan_tag}]", COLORS_NORMAL[0]),
                        (do_trim(fragger_info.name), COLORS_NORMAL[0]),
                    ]
                else:
                    cn = [(do_trim(fragger_info.name), COLORS_NORMAL[0])]

                line.extend(cn)
                line.extend(
                    [
                        5,
                        (ally_icon, 4, 1),
                        5,
                        (TIER_ROMAN[f_level - 1], COLORS_NORMAL[0]),
                        5,
                        (f_name, COLORS_NORMAL[0]),
                        5,
                        (death_icon, -3, 1),
                        5,
                    ]
                )

                if killed_info.clan_tag:
                    cn = [
                        (f"[{killed_info.clan_tag}]", COLORS_NORMAL[1]),
                        (do_trim(killed_info.name), COLORS_NORMAL[1]),
                    ]
                else:
                    cn = [(do_trim(killed_info.name), COLORS_NORMAL[1])]
                line.extend(cn)
                line.extend(
                    [
                        5,
                        (enemy_icon, 4, 1),
                        5,
                        (TIER_ROMAN[k_level - 1], COLORS_NORMAL[1]),
                        5,
                        (k_name, COLORS_NORMAL[1]),
                    ]
                )
            else:
                ally_icon = self._renderer.resman.load_image(
                    f"{k_species}.png", rot=-90, path=f"{icon_res}.ally"
                )
                enemy_icon = self._renderer.resman.load_image(
                    f"{f_species}.png", rot=90, path=f"{icon_res}.enemy"
                )

                if fragger_info.clan_tag:
                    cn = [
                        (f"[{fragger_info.clan_tag}]", COLORS_NORMAL[1]),
                        (do_trim(fragger_info.name), COLORS_NORMAL[1]),
                    ]
                else:
                    cn = [(do_trim(fragger_info.name), COLORS_NORMAL[1])]

                line.extend(cn)
                line.extend(
                    [
                        5,
                        (enemy_icon, 4, 1),
                        5,
                        (TIER_ROMAN[f_level - 1], COLORS_NORMAL[1]),
                        5,
                        (f_name, COLORS_NORMAL[1]),
                        5,
                        (death_icon, -3, 1),
                        5,
                    ]
                )

                if killed_info.clan_tag:
                    cn = [
                        (f"[{killed_info.clan_tag}]", COLORS_NORMAL[0]),
                        (do_trim(killed_info.name), COLORS_NORMAL[0]),
                    ]
                else:
                    cn = [(do_trim(killed_info.name), COLORS_NORMAL[0])]
                line.extend(cn)
                line.extend(
                    [
                        5,
                        (ally_icon, 4, 1),
                        5,
                        (TIER_ROMAN[k_level - 1], COLORS_NORMAL[0]),
                        5,
                        (k_name, COLORS_NORMAL[0]),
                    ]
                )
            line_img = self.build(line)
            y_pos -= line_img.height
            x_pos = (image.width - 30) - line_img.width
            image.paste(line_img, (x_pos, y_pos), line_img)

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
        line_hash = self._hash(line)

        if line_hash in self._generated_lines:
            return self._generated_lines[line_hash]

        ib = Image.new("RGBA", (560, 17))
        ibd = ImageDraw.Draw(ib)

        pos_x = 0

        for el in line:
            if isinstance(el, tuple):
                if len(el) == 2:
                    a, b = el
                    if isinstance(a, str) and isinstance(b, str):
                        str_w, str_h = self._font.getsize(a)
                        ibd.text((pos_x, 0), a, b, self._font)
                        pos_x += str_w
                elif len(el) == 3:
                    a, b, c = el
                    pattern_image = [
                        isinstance(a, Image.Image),
                        isinstance(b, int),
                        isinstance(c, int),
                    ]
                    if pattern_image:
                        nw, nh = round(a.width * c), round(a.height * c)
                        a = a.resize((nw, nh), Image.LANCZOS)
                        ib.paste(a, (pos_x, b), a)
                        pos_x += a.width
            elif isinstance(el, int):
                pos_x += el
        ib = ib.crop((0, 0, pos_x, ib.height))
        self._generated_lines[line_hash] = ib.copy()
        return ib.copy()
