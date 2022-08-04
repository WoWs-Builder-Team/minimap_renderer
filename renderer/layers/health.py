import numpy as np

from typing import Union
from renderer.data import PlayerInfo
from renderer.render import Renderer
from renderer.base import LayerBase
from renderer.const import RELATION_NORMAL_STR, COLORS_NORMAL
from PIL import Image, ImageDraw, ImageColor
from math import floor


class LayerHealthBase(LayerBase):
    def __init__(self, renderer: Renderer):
        self._renderer = renderer
        self._ships = renderer.resman.load_json(
            self._renderer.res, "ships.json"
        )
        self._player: Union[PlayerInfo, None] = None
        self._font = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=16
        )
        self._green = ImageColor.getrgb("#4ce8aaff")
        self._yellow = ImageColor.getrgb("#ffc400ff")
        self._red = ImageColor.getrgb("#fe4d2aff")
        self._color_regen_max = ImageColor.getrgb("#ffffffc3")
        self.prepare()

    def prepare(self):
        self._player = [
            p
            for p in self._renderer.replay_data.player_info.values()
            if p.relation == -1
        ].pop()

    def draw(self, game_time: int, image: Image.Image):
        assert self._player
        ships = self._renderer.replay_data.events[game_time].evt_vehicle
        ship = ships[self._player.ship_id]
        per = ship.health / self._player.max_health
        index, name, species, level = self._ships[self._player.ship_params_id]

        bar_res = f"{self._renderer.res}.ship_bars"
        suffix_fg = "_h"
        suffix_bg = "_h_bg" if ship.is_alive else "_h_bgdead"

        bg = self._renderer.resman.load_image(
            bar_res, f"{index}{suffix_bg}.png", nearest=False
        )

        fg = self._renderer.resman.load_image(
            bar_res, f"{index}{suffix_bg}.png", size=bg.size, nearest=False
        )

        maxHeal = floor(20) * 0.02 * self._player.max_health
        canHeal = (
            ship.regeneration_health
            if ship.regeneration_health < maxHeal
            else maxHeal
        )

        per_limit = (canHeal + ship.health) / self._player.max_health

        if per > 0.8:
            bar_color = self._green
        elif 0.8 >= per > 0.3:
            bar_color = self._yellow
        else:
            bar_color = self._red

        if ship.is_alive:

            regen_limit_arr = np.array(fg)
            regen_limit_arr[
                regen_limit_arr[:, :, 3] > 75
            ] = self._color_regen_max
            regen_limit_img = Image.fromarray(regen_limit_arr)
            mask_r_limit = Image.new(bg.mode, bg.size)
            mask_r_limit_draw = ImageDraw.Draw(mask_r_limit)
            mask_r_limit_draw.rectangle(
                ((0, 0), (round(bg.width * per_limit), bg.width)),
                fill=self._color_regen_max,
            )
            bg.paste(regen_limit_img, mask=mask_r_limit)

            fg_arr = np.array(fg)
            fg_arr[fg_arr[:, :, 3] > 75] = bar_color
            bar = Image.fromarray(fg_arr)
            mask = Image.new(bg.mode, bg.size)
            mask_w = mask.width * per
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rectangle(((0, 0), (mask_w, mask.width)), fill="black")

            bg.paste(bar, mask=mask)
        px = 940 - round(bg.width / 2)

        hp_current = "{:,}".format(round(ship.health)).replace(",", " ")
        hp_max = "{:,}".format(round(self._player.max_health)).replace(
            ",", " "
        )
        hp_max_text = f"/{hp_max}"

        hp_c_w, hp_c_h = self._font.getsize(hp_current)
        hp_w, hp_h = self._font.getsize(hp_max_text)
        n_w, n_h = self._font.getsize(name)

        bg = bg.resize((235, 62), resample=Image.LANCZOS)

        th = Image.new("RGBA", (bg.width, max(hp_h, n_h, hp_c_h)))
        th_draw = ImageDraw.Draw(th)

        th_draw.text((0, 0), name, fill="white", font=self._font)
        th_draw.text(
            (th.width - (hp_w + hp_c_w), 0),
            hp_current,
            fill=bar_color,
            font=self._font,
        )
        th_draw.text(
            (th.width - hp_w, 0),
            hp_max_text,
            fill=self._green,
            font=self._font,
        )

        image.paste(th, (px, 90), th)
        image.paste(bg, (px, 30), bg)
