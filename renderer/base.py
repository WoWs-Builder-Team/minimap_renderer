from typing import Any, Generator, Union, Optional
from abc import ABC, abstractmethod
from .data import ReplayData
from PIL import Image, ImageDraw
from .resman import ResourceManager


class LayerBase(ABC):
    """A template for Layer classes"""

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def draw(
        self, game_time: int, arg: Union[Image.Image, ImageDraw.ImageDraw]
    ):
        """_summary_

        Args:
            game_time (int): Used to sync events.
            arg (Union[Image.Image, ImageDraw.ImageDraw]): Depends on how the
            layer elements will be draw.
        """
        pass
