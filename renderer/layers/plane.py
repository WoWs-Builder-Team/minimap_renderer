import numpy as np

from renderer.data import Plane
from renderer.render import Renderer
from renderer.base import LayerBase
from renderer.const import RELATION_NORMAL_STR

from PIL import Image


class LayerPlaneBase(LayerBase):
    """A class that handles/draws planes.

    Args:
        LayerBase (_type_): _description_
    """

    def __init__(self, renderer: Renderer):
        """Initiates this class.

        Args:
            renderer (Renderer): The renderer.
        """
        self._renderer = renderer
        self._planes = renderer.resman.load_json("planes.json")

    def draw(self, game_time: int, image: Image.Image):
        """Draws the planes to the minimap image.

        Args:
            game_time (int): Game time.
            image (Image.Image): The minimap image.
        """
        planes = self._renderer.replay_data.events[game_time].evt_plane

        if not planes:
            return

        for plane in planes.values():
            x, y = self._renderer.get_scaled(plane.position)
            icon = self._get_plane_icon(plane)
            m1 = round(icon.width / 2)
            m2 = round(icon.height / 2)
            image.paste(icon, (x - m1, y - m2), icon)

    def _get_plane_icon(self, plane: Plane) -> Image.Image:
        """Loads the plane icon from the resources.

        Args:
            plane (Plane): Plane data.

        Returns:
            Image.Image: The image of the plane.
        """
        ptype, ammo = self._planes[plane.params_id]
        relation = RELATION_NORMAL_STR[plane.relation]
        icon_res = f"plane_icons.{relation}"

        if plane.purpose in [0, 1]:
            if ptype == "Dive":
                filename = f"Dive_{ammo}.png"
                icon = self._renderer.resman.load_image(
                    filename, path=icon_res
                )
            else:
                filename = f"{ptype}.png"
                icon = self._renderer.resman.load_image(
                    filename, path=icon_res
                )
        elif plane.purpose in [2, 3]:
            icon = self._renderer.resman.load_image("Cap.png", path=icon_res)
        else:
            if plane.purpose == 6:
                filename = f"Airstrike_{ammo}.png"
                icon = self._renderer.resman.load_image(
                    filename, path=icon_res
                )
            else:
                filename = "Scout.png"
                icon = self._renderer.resman.load_image(
                    filename, path=icon_res
                )

        if plane.purpose == 1:
            icon_px = np.array(icon)
            icon_px[icon_px[:, :, 3] == 255, 3] = 64
            icon = Image.fromarray(icon_px, mode="RGBA")

        return icon
