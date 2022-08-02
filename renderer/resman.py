import json

from importlib.resources import open_text, open_binary
from PIL import Image
from typing import Optional


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

    def load_image(
        self,
        package: str,
        filename: str,
        size: Optional[tuple[int, int]] = None,
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
        if size:
            key_name = f"{package}.{filename}.{'.'.join(map(str, size))}"
        else:
            key_name = f"{package}.{filename}"

        if key_name in self._resources:
            return self._resources[key_name].copy()
        else:
            with open_binary(package, filename) as br:
                image = Image.open(br)

                if size:
                    image = image.resize(size, Image.LANCZOS)

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
