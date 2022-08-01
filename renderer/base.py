from typing import Any, Generator, Union, Optional
from abc import ABC, abstractmethod
from .data import ReplayData
from PIL import Image, ImageDraw
from .resman import ResourceManager


class RendererBase(ABC):
    """A template for Renderer classes"""

    replay_data: ReplayData
    res: str
    minimap_image: Optional[Image.Image]
    minimap_size: int
    space_size: int
    scaling: float
    resman: ResourceManager

    @abstractmethod
    def __init__(self, replay_data: ReplayData):
        pass

    @abstractmethod
    def start(self):
        """
        Starts the renderer.
        """
        pass

    @abstractmethod
    def _load_map(self):
        """
        Loads the map.
        """
        pass


class LayerBase(ABC):
    """A template for Layer classes"""

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def draw(
        self, game_time: int, arg: Union[Image.Image, ImageDraw.ImageDraw]
    ):
        """Template

        Args:
            game_time (int): Used to sync events.
            arg (Union[Image.Image, ImageDraw.ImageDraw]): Depends on how the
            layer elements will be draw.
        """
        pass
