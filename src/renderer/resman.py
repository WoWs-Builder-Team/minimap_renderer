import json

from renderer.utils import LOGGER
from importlib.resources import open_text, open_binary, is_resource
from PIL import Image
from typing import Optional
from PIL import ImageFont
from langdetect import detect, LangDetectException
from hanzidentifier import has_chinese
from renderer.data import Message

class ResourceManager:
    """A resource manager."""

    def __init__(self, version: str):
        """Initializes this class."""
        self._cache = {}
        self._default_res = f"{__package__}.resources"
        self._versions = version
        self.render_scale = 1.0

    def set_render_scale(self, scale: float):
        if scale <= 0:
            raise ValueError("render scale must be greater than 0")
        self.render_scale = scale

    def load_json(
        self,
        filename: str,
        path: Optional[str] = None,
        ignore_versioned: bool = False,
    ) -> dict:
        """Loads a json file from the given package and converts its numeric
        keys to integer.
        """
        key = f"{path}.{filename}"
        if cached := self._cache.get(key, None):
            return cached

        try:
            if ignore_versioned:
                raise ModuleNotFoundError

            res_package = f"{__package__}.versions.{self._versions}.resources"
            res_package = res_package if not path else f"{res_package}.{path}"

            if not is_resource(res_package, filename):
                raise FileNotFoundError
        except (FileNotFoundError, ModuleNotFoundError):
            res_package = self._default_res
            res_package = res_package if not path else f"{res_package}.{path}"

        with open_text(res_package, filename) as tr:
            data = json.load(tr, object_hook=self.key_converter)
            self._cache[key] = data
            return data

    def load_font(
        self, filename: str, path: Optional[str] = None, size=12
    ) -> ImageFont.FreeTypeFont:
        physical_size = max(1, round(size * self.render_scale))
        key = f"{path}.{filename}.{physical_size}"
        if cached := self._cache.get(key, None):
            return cached

        try:
            res_package = f"{__package__}.versions.{self._versions}.resources"
            res_package = res_package if not path else f"{res_package}.{path}"

            if not is_resource(res_package, filename):
                raise FileNotFoundError
            LOGGER.debug(f"Versioned {filename} found.")
        except (FileNotFoundError, ModuleNotFoundError):
            res_package = self._default_res
            res_package = res_package if not path else f"{res_package}.{path}"

        with open_binary(res_package, filename) as fr:
            data = ImageFont.truetype(fr, size=physical_size)
            self._cache[key] = data
            return data

    def load_default_font(self, size=12) -> ImageFont.FreeTypeFont:
        """Loads the default font.

        Returns:
            ImageFont.FreeTypeFont: The font.
        """
        return self.load_font(filename="warhelios_bold.ttf", size=size)

    def load_font_with_text(self, text: str, size=12) -> ImageFont.FreeTypeFont:
        """Pick the font based on the message language.

        Args:
            text (str): The pure text.

        Returns:
            ImageFont.FreeTypeFont: The font.
        """
        return self._select_font_by_text(text, size)

    def _select_font_by_text(self, text: str, size: int) -> ImageFont.FreeTypeFont:
        """Select the font based on the text language.

        Args:
            text (str): The text.

        Returns:
            ImageFont.FreeTypeFont: The font.
        """
        try:
            language = detect(text)  # this can detect Chinese as Korean
            if has_chinese(text):
                return self.load_font(
                    filename="warhelios_bold_zh.ttf", size=size
                )

            if language == "ja":
                return self.load_font(
                    filename="warhelios_bold_jp.ttf", size=size
                )
            elif language == "ko":
                return self.load_font(
                    filename="warhelios_bold_ko.ttf", size=size
                )
        except LangDetectException:
            LOGGER.warn(f"Unable to detect language of message \"{text}\"")

        # fallback to the default font
        return self.load_default_font(size=size)

    def load_image(
        self,
        filename: str,
        path: Optional[str] = None,
        nearest=False,
        size: Optional[tuple[int, int]] = None,
        rot: Optional[int] = None,
        readonly: bool = True,
    ) -> Image.Image:
        """Loads the image from the package or from the memory.

        Args:
            package (str): Package where the image will be loaded.
            filename (str): The filename of the image.
            size (Optional[tuple[int, int]], optional): If provided, loaded
            image will be resized. Defaults to None.
            readonly (bool): If True, returns cached reference without copying.

        Returns:
            Image.Image: The loaded image.
        """
        key = [filename]

        if path:
            key = [path, filename]

        if size:
            key.append("_".join(map(str, size)))

        if rot:
            key.append(str(rot))

        key.extend((str(nearest), str(self.render_scale)))
        key_name = "_".join(key)

        if key_name in self._cache:
            img = self._cache[key_name]
            return img if readonly else img.copy()

        try:
            res_package = f"{__package__}.versions.{self._versions}.resources"
            res_package = res_package if not path else f"{res_package}.{path}"

            if not is_resource(res_package, filename):
                raise FileNotFoundError
            LOGGER.debug(f"Versioned {filename} found.")
        except (FileNotFoundError, ModuleNotFoundError):
            res_package = self._default_res
            res_package = res_package if not path else f"{res_package}.{path}"

        with open_binary(res_package, filename) as br:
            image = Image.open(br)
            image.load()

            if image.mode != "RGBA":
                image = image.convert("RGBA")
            if size:
                image = image.resize(
                    size,
                    Image.Resampling.LANCZOS
                    if not nearest
                    else Image.Resampling.NEAREST,
                )
            elif self.render_scale != 1:
                image = image.resize(
                    (
                        max(1, round(image.width * self.render_scale)),
                        max(1, round(image.height * self.render_scale)),
                    ),
                    Image.Resampling.NEAREST
                    if nearest
                    else Image.Resampling.LANCZOS,
                )
            if rot:
                image = image.rotate(
                    rot, resample=Image.Resampling.BICUBIC, expand=True
                )

            self._cache[key_name] = image
            return image if readonly else image.copy()

    @staticmethod
    def key_converter(o):
        """Converts numeric keys to integer.

        Args:
            o (_type_): dict

        Returns:
            _type_: dict
        """
        temp = {}
        for k, v in o.items():
            if k.isdigit():
                temp[int(k)] = v
            else:
                temp[k] = v
        return temp
