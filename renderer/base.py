from typing import Any, Generator, Union
from abc import ABC, abstractmethod
from .data import ReplayData
from PIL import Image


class RendererBase(ABC):
    """A template for Renderer classes"""

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
    def generator(
        self, game_time: int
    ) -> Union[Generator[Any, None, None], Image.Image]:
        """
        Yields whatever the fuck it wants to yield.
        :return: A generator.
        """
        pass
