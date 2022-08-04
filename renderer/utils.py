import json
import logging
import numpy as np

from importlib.resources import open_binary, open_text
from PIL import Image, ImageDraw, ImageFont, ImageColor
from .data import PlayerInfo
from .const import COLORS_NORMAL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger("renderer")


def draw_grid() -> Image.Image:
    """Draws a grid to the image and returns it.

    Returns:
        Image.Image: An image with grid on it.
    """
    base = Image.new("RGBA", (760, 760))
    draw = ImageDraw.Draw(base)
    for x in range(0, 760, round(760 / 10)):
        if x == 0:
            continue
        draw.line([(x, 0), (x, base.height)], fill="#ffffff40")
        draw.line([(0, x), (base.width, x)], fill="#ffffff40")
    # draw.rectangle((0, 0, base.width - 1, base.height - 1),
    #                outline="#ffffff40", width=1)
    return base.copy()


def generate_ship_data(
    player_info: dict[int, PlayerInfo]
) -> dict[int, Image.Image]:
    """Gets ship information and creates and image with the ship name on it.

    Args:
        player_info (dict[int, PlayerInfo]): Player's information.

    Returns:
        dict[int, tuple[str, str, int, Image.Image]]: Ship's information with
        an image with the ships name on it.
    """
    dict_player_holder: dict[int, Image.Image] = {}
    text_offset = 16
    hw, hh = (100, 100)
    res_path = "renderer.resources"

    with open_text(res_path, "ships.json") as text_reader:
        ships = json.load(text_reader)

    with open_binary(res_path, "warhelios_bold.ttf") as binary_reader:
        font = ImageFont.FreeTypeFont(binary_reader, size=12)

    for player in player_info.values():
        font_color = COLORS_NORMAL[player.relation]
        index, ship_name, ship_species, ship_level = ships[
            str(player.ship_params_id)
        ]
        holder: Image.Image = Image.new("RGBA", (hw, hh))
        holder_draw: ImageDraw.ImageDraw = ImageDraw.Draw(holder)
        text_w, text_h = holder_draw.textsize(text=ship_name, font=font)
        text_x = round((hw / 2) - (text_w / 2))
        text_y = round((hh - text_h) - text_offset)
        holder_draw.text(
            xy=(text_x, text_y), text=ship_name, fill=font_color, font=font
        )
        dict_player_holder[player.avatar_id] = holder
    return dict_player_holder


def paste_args_centered(
    image: Image.Image, x: int, y: int, masked=False
) -> dict:
    """Returns named arguments for Image.paste.

    Args:
        image (Image.Image): Image to paste.
        x (_type_): x position.
        y (_type_): y position.
        masked (bool, optional): If masked. Defaults to False.

    Returns:
        dict: Named arguments for Image.paste.
    """

    o = 0  # offset for the legends
    result = {
        "im": image,
        "box": (
            (x - round(image.width / 2)) + o,
            (y - round(image.height / 2)) + o,
        ),
    }
    if masked:
        result.update({"mask": image})
    return result


def paste_centered(
    bg: Image.Image, fg: Image.Image, masked=False
) -> Image.Image:
    """Paste fg on top of bg.

    Args:
        bg (Image.Image): Image to be pasted on.
        fg (Image.Image): Image to be pasted to.
        masked (bool, optional): If masked. Defaults to False.

    Returns:
        Image.Image: Combined images.
    """
    x = round(bg.width / 2 - fg.width / 2)
    y = round(bg.height / 2 - fg.height / 2)
    bg.paste(fg, (x, y), mask=fg if masked else None)
    return bg


def draw_health_bar(
    image: Image.Image, width=50, height=5, y_pos=65, color="red", hp_per=1.0
):
    """Draws a health bar to the image given.

    Args:
        image (Image.Image): The image where the health bar will be draw on.
        width (int, optional): Width of the health bar. Defaults to 50.
        height (int, optional): Height of the health bar. Defaults to 5.
        y_pos (int, optional): Y position of the health bar. Defaults to 65.
        color (str, optional): The color of the health bar. Defaults to "red".
        hp_per (float, optional): Hit points for the health bar.
        Defaults to 1.0.
    """
    draw = ImageDraw.Draw(image)
    assert width <= image.width
    assert y_pos < image.height - height
    x1 = image.width / 2 - width / 2
    y1 = y_pos
    x2 = ((image.width / 2 + width / 2) - x1) * hp_per + x1
    y2 = y_pos + height
    xy1 = (x1, y1, x2, y2)
    xy2 = (x1, y1, (image.width / 2 + width / 2), y2)
    draw.rectangle(xy=xy1, fill=color)
    draw.rectangle(xy=xy2, outline=color, width=1)


def replace_color(img: Image.Image, from_color: str, to_color: str):
    """
    Replaces the color from the image. The image should not be anti-aliased.
    :param img:
    :param from_color:
    :param to_color:
    :return:
    """

    f_color = ImageColor.getrgb(from_color)
    t_color = ImageColor.getrgb(to_color)

    data = np.array(img)
    red, green, blue = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    mask = (red == f_color[0]) & (blue == f_color[1]) & (green == f_color[2])
    data[:, :, :3][mask] = t_color
    return Image.fromarray(data)


def flip_y(n: tuple):
    """Yes. Move along.

    Args:
        n (tuple): Yes.

    Returns:
        _type_: Yes.
    """
    return n[0], -n[1]


def getEquidistantPoints(
    p1: tuple[float, float], p2: tuple[float, float], parts: int
):
    """Generates equidistant points.

    Args:
        p1 (tuple[float, float]): Point 1
        p2 (tuple[float, float]): Point 2
        parts (int): Number of points between point 1 & 2.

    Returns:
        _type_: An iterator the iterates the points between 1 & 2.
    """
    return zip(
        np.round(np.linspace(p1[0], p2[0], parts + 1)),
        np.round(np.linspace(p1[1], p2[1], parts + 1)),
    )
