from PIL import Image
from renderer.base import LayerBase
from renderer.render import Renderer


class LayerWardBase(LayerBase):
    """A class that handles/draws wards (dropped fighters).

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(self, renderer: Renderer):
        """Initializes this class.

        Args:
            renderer (Renderer): _description_
        """
        self._renderer = renderer

    def draw(self, game_time: int, image: Image.Image):
        """Draws the wards to the minimap.

        Args:
            game_time (int): The game time.
            image (Image.Image): The minimap image.

        Returns:
            _type_: _description_
        """

        events = self._renderer.replay_data.events
        wards = events[game_time].evt_ward.values()

        if not wards:
            return

        for ward in wards:
            x, y = self._renderer.get_scaled(ward.position)
            w = h = round(self._renderer.get_scaled_r(ward.radius) * 2 + 2)
            w1 = round(w / 2)
            h1 = round(h / 2)

            filename = (
                "ward_ally" if ward.relation in [-1, 0] else "ward_enemy"
            )
            ward_image = self._renderer.resman.load_image(
                f"{filename}.png", size=(w, h)
            )

            image.paste(
                ward_image,
                (
                    x - w1,
                    y - h1,
                ),
                ward_image,
            )
