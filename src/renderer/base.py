from abc import ABC, abstractmethod
from PIL import Image, ImageDraw


class LayerBase(ABC):
    """A template for Layer classes"""

    @abstractmethod
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def draw(self, game_time: int, arg: Image.Image | ImageDraw.ImageDraw):
        """_summary_

        Args:
            game_time (int): Used to sync events.
            arg (Union[Image.Image, ImageDraw.ImageDraw]): Depends on how the
            layer elements will be draw.
        """
        raise NotImplementedError
