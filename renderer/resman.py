import json

from renderer.utils import LOGGER
from importlib.resources import open_text, open_binary, is_resource
from PIL import Image
from typing import Optional
from PIL import ImageFont


class ResourceManager:
    """A resource manager."""

    def __init__(self, version: str):
        """Initializes this class."""
        self._cache = {}
        self._default_res = f"{__package__}.resources"
        self._versions = version

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
        key = f"{path}.{filename}.{size}"
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
            data = ImageFont.truetype(fr, size=size)
            self._cache[key] = data
            return data

    def load_image(
        self,
        filename: str,
        path: Optional[str] = None,
        nearest=False,
        size: Optional[tuple[int, int]] = None,
        rot: Optional[int] = None,
    ) -> Image.Image:
        """Loads the image from the package or from the memory.

        Args:
            package (str): Package where the image will be loaded.
            filename (str): The filename of the image.
            size (Optional[tuple[int, int]], optional): If provided, loaded
            image will be resized. Defaults to None.

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

        key.append(str(nearest))
        key_name = "_".join(key)

        if key_name in self._cache:
            return self._cache[key_name].copy()

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

            if image.mode != "RGBA":
                image = image.convert("RGBA")
            if size:
                image = image.resize(
                    size,
                    Image.Resampling.LANCZOS
                    if not nearest
                    else Image.Resampling.NEAREST,
                )
            if rot:
                image = image.rotate(
                    rot, resample=Image.Resampling.BICUBIC, expand=True
                )

            self._cache[key_name] = image.copy()
            return image.copy()

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
