import json

from importlib.resources import open_text, open_binary
from PIL import Image
from typing import Optional


class ResourceManager:
    def __init__(self) -> None:
        self._resources = {}

    def load_json(self, package: str, filename: str) -> dict:
        with open_text(package, filename) as tr:
            return json.load(tr)

    def load_image(
        self,
        package: str,
        filename: str,
        size: Optional[tuple[int, int]] = None,
    ) -> Image.Image:
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
