"""
quick and dirty script to generate these letters
"""

from PIL import Image, ImageDraw, ImageFont

from renderer import const


font = ImageFont.truetype("../warhelios_bold.ttf", 25)


for key, name in const.RELATION_NORMAL_STR.items():
    color = const.COLORS_NORMAL[key]

    for offset in range(26):  # guess we'll do every letter to be safe
        image = Image.new("RGBA", (100, 100))
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), chr(ord('A') + offset), fill=color, font=font)

        width, height = image.size
        minx = min(x for x in range(width) for y in range(height) if image.getpixel((x, y)) != (0, 0, 0, 0))
        maxx = max(x for x in range(width) for y in range(height) if image.getpixel((x, y)) != (0, 0, 0, 0))
        miny = min(y for x in range(width) for y in range(height) if image.getpixel((x, y)) != (0, 0, 0, 0))
        maxy = max(y for x in range(width) for y in range(height) if image.getpixel((x, y)) != (0, 0, 0, 0))

        image = image.crop((minx, miny, maxx + 1, maxy + 1))

        image.save(f"{name}/lettered_{offset}.png")
