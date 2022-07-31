import json

from typing import Optional
from importlib.resources import open_text
from renderer.base import RendererBase
from renderer.data import ReplayData
from renderer.utils import load_image, draw_grid
from renderer.layers import LayerShip, LayerSmoke, LayerShot, LayerTorpedo
from PIL import Image, ImageDraw
from imageio_ffmpeg import write_frames
from renderer.resman import ResourceManager


class Renderer(RendererBase):
    def __init__(self, replay_data: ReplayData):
        """Orchestrates the rendering process.

        Args:
            replay_data (ReplayData): Replay data.
        """
        self.replay_data: ReplayData = replay_data
        self.res: str = f"{__package__}.resources"
        # MAP INFO
        self.minimap_image: Optional[Image.Image] = None
        self.minimap_size: int = 0
        self.space_size: int = 0
        self.scaling: float = 0.0
        self.resman = ResourceManager()

    def start(self):
        """Starts the rendering process"""
        self._load_map()
        assert self.minimap_image

        layer_ship = LayerShip(self)
        layer_shot = LayerShot(self)
        layer_torpedo = LayerTorpedo(self)
        layer_smoke = LayerSmoke(self)

        video_writer = write_frames(
            path="minimap.mp4",
            fps=20,
            quality=9,
            pix_fmt_in="rgba",
            macro_block_size=19,
            size=self.minimap_image.size,
        )
        video_writer.send(None)

        for game_time in self.replay_data.events.keys():
            minimap_img = self.minimap_image.copy()
            draw = ImageDraw.Draw(minimap_img)
            layer_shot.draw(game_time, draw)
            layer_torpedo.draw(game_time, draw)
            layer_ship.draw(game_time, minimap_img)
            layer_smoke.draw(game_time, minimap_img)
            video_writer.send(minimap_img.tobytes())
        video_writer.close()

    def _load_map(self):
        """Loads and prepares the map."""
        with open_text(f"{self.res}.spaces", "manifest.json") as reader:
            manifest = json.load(reader)
            self.minimap_size, self.space_size, self.scaling = manifest[
                self.replay_data.game_map
            ]

        map_res = f"{self.res}.spaces.{self.replay_data.game_map}"
        map_land = load_image(map_res, "minimap.png")
        map_water = load_image(map_res, "minimap_water.png")
        map_water = Image.alpha_composite(map_water, draw_grid())
        self.minimap_image = Image.alpha_composite(map_water, map_land)
        # draw = ImageDraw.Draw(self._minimap_image)
        # draw.ellipse(xy=[(2, 760 / 2), (2, 760 / 2 + 2)], fill="white")
