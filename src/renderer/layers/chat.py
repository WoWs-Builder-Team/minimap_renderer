from typing import Optional
from PIL import Image, ImageDraw
from renderer.base import LayerBase
from renderer.const import COLORS_NORMAL
from renderer.data import Message, ReplayData
from renderer.render import Renderer
from functools import lru_cache

class LayerChatBase(LayerBase):
    """The class for handling in-game chat messages.

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
        self._font = None # to be decided per message
        self._players = self._replay_data.player_info
        self._generated_lines: dict[int, Image.Image] = {}
        self._messages: list[Message] = []
        # self._lines: dict[int, Image.Image] = {}

    def draw(self, game_time: int, image: Image.Image):
        """Draw the in-game chat to the image.

        Args:
            game_time (int): The game time.
            image (Image.Image): The image where the chat will be pasted to,
        """
        evt_messages = self._replay_data.events[game_time].evt_chat
        self._messages.extend(evt_messages)

        x_pos = 805
        y_pos = image.height - 5

        for message in reversed(self._messages[-5:]):

            line = self.build(message)
            _, l_h = line.size
            y_pos -= l_h
            image.alpha_composite(line, (x_pos, y_pos))

    @lru_cache
    def build(self, message: Message) -> Image.Image:
        """Builds the line message as an image.

        Args:
            message (Message): The message.

        Returns:
            Image.Image: Image of the chat message.
        """

        # m_hash = hash(message) & 1000000000

        # if image := self._lines.get(m_hash, None):
        #     return image

        self._font = self._renderer.resman.load_font_with_text(
            message.message, size=12
        )
        base = Image.new("RGBA", (560, 17))
        draw = ImageDraw.Draw(base)
        player = self._players[message.player_id]

        x_pos = 0

        if self._renderer.anon and player.clan_tag:
            clan_tag = "#" * len(player.clan_tag)
        elif player.clan_tag:
            clan_tag = player.clan_tag
        else:
            clan_tag = ""

        if player.clan_tag:
            c_w, _ = self._font.getbbox(f"[{clan_tag}]")[2:]
            draw.text(
                (x_pos, 0),
                f"[{clan_tag}]",
                self.unpack_color(player.clan_color),
                self._font,
            )
            x_pos += c_w

        n_color = (
            COLORS_NORMAL[0]
            if player.relation in [-1, 0]
            else COLORS_NORMAL[1]
        )

        if self._renderer.anon:
            name = self._renderer.usernames[player.id]
        else:
            name = player.name

        n_w, _ = self._font.getbbox(f"{name}: ")[2:]
        draw.text((x_pos, 0), f"{name}: ", n_color, self._font)
        x_pos += n_w

        if message.namespace == "battle_common":
            m_color = "white"
        else:
            m_color = n_color

        m_w, _ = self._font.getbbox(message.message)[2:]
        text = message.message

        if x_pos + m_w + 805 > 1330:
            for i in range(1, len(message.message)):
                n_t = f"{message.message[:-i]}..."
                m_w, _ = self._font.getbbox(n_t)[2:]

                if x_pos + m_w + 805 <= 1330:
                    text = n_t
                    break

        draw.text((x_pos, 0), text, m_color, self._font)
        x_pos += m_w
        # self._lines[m_hash] = base
        return base

    @staticmethod
    def unpack_color(packed_value: int) -> tuple:
        """Unpacks packed color integer as RGB component.

        Args:
            packed_value (int): The packed color integer.

        Returns:
            tuple: RGB component.
        """
        bits = [8, 8, 8]
        values = []
        for bit in bits:
            value = packed_value & (2**bit - 1)
            packed_value = packed_value >> bit
            values.append(value)
        return tuple(reversed(values))
