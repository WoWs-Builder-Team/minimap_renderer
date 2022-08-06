import json

from importlib.resources import open_text, open_binary
from PIL import Image
from typing import Optional
from PIL import ImageFont


class ResourceManager:
    """A resource manager."""

    def __init__(self):
        """Initializes this class."""
        self._resources = {}

    def load_json(self, package: str, filename: str) -> dict:
        """Loads a json file from the given package and converts its numeric
        keys to integer.
        """
        with open_text(package, filename) as tr:
            return json.load(tr, object_hook=self.key_converter)

    def load_font(self, filename, package=f"{__package__}.resources", size=12):
        with open_binary(package, filename) as fr:
            return ImageFont.truetype(fr, size=size)

    def load_image(
        self,
        package: str,
        filename: str,
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
        for_key = [package, filename]

        if size:
            for_key.append(".".join(map(str, size)))
            # key_name = (
            #     f"{package}.{filename}.{'.'.join(map(str, size))}.{nearest}"
            # )
        # else:
        #     for
        #     key_name = f"{package}.{filename}.{nearest}"
        if rot:
            for_key.append(str(rot))

        for_key.append(str(nearest))
        key_name = ".".join(for_key)

        if key_name in self._resources:
            return self._resources[key_name].copy()
        else:
            with open_binary(package, filename) as br:
                image = Image.open(br)

                if image.mode != "RGBA":
                    image = image.convert("RGBA")

                if size:
                    image = image.resize(
                        size, Image.LANCZOS if not nearest else Image.NEAREST
                    )
                if rot:
                    image = image.rotate(
                        rot, resample=Image.BICUBIC, expand=True
                    )

                self._resources[key_name] = image.copy()
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
