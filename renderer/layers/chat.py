from typing import Union

from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.const import (
    COLORS_NORMAL,
    DEATH_TYPES,
    TIER_ROMAN,
)
from renderer.data import Message
from renderer.render import Renderer
from renderer.utils import do_trim


class LayerChatBase(LayerBase):
    def __init__(self, renderer: Renderer):
        self._renderer = renderer
        self._font = self._renderer.resman.load_font(
            filename="warhelios_bold.ttf", size=12
        )
        self._ships = self._renderer.resman.load_json("ships.json")
        self._players = renderer.replay_data.player_info
        self._generated_lines: dict[int, Image.Image] = {}
        self._messages: list[Message] = []
        self._lines: dict[int, Image.Image] = {}

    def _draw_separator(self):
        assert self._renderer.minimap_bg
        draw = ImageDraw.Draw(self._renderer.minimap_bg)
        draw.line(((830, 760), (1330, 760)), fill="white", width=5)

    def draw(self, game_time: int, image: Image.Image):
        evt_messages = self._renderer.replay_data.events[game_time].evt_chat
        self._messages.extend(evt_messages)

        x_pos = 805
        y_pos = 760

        for message in reversed(self._messages[-5:]):

            line = self.build(message)
            l_w, l_h = line.size
            y_pos -= l_h
            image.paste(line, (x_pos, y_pos), line)

    def build(self, message: Message):
        m_hash = hash(message) & 1000000000

        if image := self._lines.get(m_hash, None):
            return image

        base = Image.new("RGBA", (560, 15))
        draw = ImageDraw.Draw(base)
        player = self._players[message.player_id]

        x_pos = 0

        if player.clan_tag:
            c_w, c_h = self._font.getsize(f"[{player.clan_tag}]")
            draw.text(
                (x_pos, 0),
                f"[{player.clan_tag}]",
                self.unpack_color(player.clan_color),
                self._font,
            )
            x_pos += c_w

        n_color = (
            COLORS_NORMAL[0]
            if player.relation in [-1, 0]
            else COLORS_NORMAL[1]
        )

        n_w, n_h = self._font.getsize(f"{player.name}: ")
        draw.text((x_pos, 0), f"{player.name}: ", n_color, self._font)
        x_pos += n_w

        if message.namespace == "battle_common":
            m_color = "white"
        else:
            m_color = n_color

        m_w, m_h = self._font.getsize(message.message)
        text = message.message

        if x_pos + m_w + 805 > 1330:
            for i in range(1, len(message.message)):
                n_t = f"{message.message[:-i]}..."
                m_w, m_h = self._font.getsize(n_t)

                if x_pos + m_w + 805 <= 1330:
                    text = n_t
                    break

        draw.text((x_pos, 0), text, m_color, self._font)
        x_pos += m_w
        self._lines[m_hash] = base
        return base

    @staticmethod
    def unpack_color(packed_value: int) -> tuple:
        bits = [8, 8, 8]
        values = []
        for bit in bits:
            value = packed_value & (2**bit - 1)
            packed_value = packed_value >> bit
            values.append(value)
        return tuple(reversed(values))
