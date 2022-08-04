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
        self._color_gray = ImageColor.getrgb("#ffffffc3")
        self._abilities = renderer.resman.load_json(
            self._renderer.res, "abilities.json"
        )
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
        ability = self._abilities[self._player.ship_params_id]
        per = ship.health / self._player.max_health
        index, name, species, level = self._ships[self._player.ship_params_id]

        bar_res = f"{self._renderer.res}.ship_bars"
        suffix_fg = "_h"
        suffix_bg = "_h_bg" if ship.is_alive else "_h_bgdead"

        bg_bar = self._renderer.resman.load_image(
            bar_res, f"{index}{suffix_bg}.png", nearest=False
        )

        fg_bar = self._renderer.resman.load_image(
            bar_res, f"{index}{suffix_fg}.png", nearest=False
        )
        fg_bar = fg_bar.resize(bg_bar.size, Image.LANCZOS)

        if per > 0.8:
            bar_color = self._green
        elif 0.8 >= per > 0.3:
            bar_color = self._yellow
        else:
            bar_color = self._red

        if ship.is_alive:
            alpha = 75
            hp_bar_arr = np.array(fg_bar)
            hp_bar_arr[hp_bar_arr[:, :, 3] > alpha] = bar_color
            hp_bar_img = Image.fromarray(hp_bar_arr)
            mask_hp_img = Image.new(fg_bar.mode, fg_bar.size)
            mask_hp_img_w = mask_hp_img.width * per
            mask_hp_draw = ImageDraw.Draw(mask_hp_img)
            mask_hp_draw.rectangle(
                ((0, 0), (mask_hp_img_w, mask_hp_img.width)), fill="black"
            )

            if 9 in ability:
                wt = ability["workTime"]
                rhs = ability["regenerationHPSpeed"]
                maxHeal = floor(wt) * rhs * self._player.max_health
                canHeal = (
                    ship.regeneration_health
                    if ship.regeneration_health < maxHeal
                    else maxHeal
                )

                per_limit = (canHeal + ship.health) / self._player.max_health

                regen_bar_arr = np.array(fg_bar)
                regen_bar_arr[
                    regen_bar_arr[:, :, 3] > alpha
                ] = self._color_gray
                regen_bar_img = Image.fromarray(regen_bar_arr)
                mask_regen_img = Image.new(fg_bar.mode, fg_bar.size)
                mask_regen_img_w = mask_regen_img.width * per_limit
                mask_regen_draw = ImageDraw.Draw(mask_regen_img)
                mask_regen_draw.rectangle(
                    ((0, 0), (mask_regen_img_w, mask_regen_img.width)),
                    fill="black",
                )

                bg_bar.paste(regen_bar_img, mask=mask_regen_img)
            bg_bar.paste(hp_bar_img, mask=mask_hp_img)

        px = 940 - round(bg_bar.width / 2)

        hp_current = "{:,}".format(round(ship.health)).replace(",", " ")
        hp_max = "{:,}".format(round(self._player.max_health)).replace(
            ",", " "
        )
        hp_max_text = f"/{hp_max}"

        hp_c_w, hp_c_h = self._font.getsize(hp_current)
        hp_w, hp_h = self._font.getsize(hp_max_text)
        n_w, n_h = self._font.getsize(name)

        bg_bar = bg_bar.resize((235, 62), resample=Image.LANCZOS)

        th = Image.new("RGBA", (bg_bar.width, max(hp_h, n_h, hp_c_h)))
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
            fill="#cdcdcd",
            font=self._font,
        )

        image.paste(th, (px, 90), th)
        image.paste(bg_bar, (px, 30), bg_bar)
