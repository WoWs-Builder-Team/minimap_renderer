import json

from typing import Optional
from importlib.resources import open_text
from renderer.base import RendererBase
from renderer.data import ReplayData
from renderer.utils import load_image, draw_grid
from renderer.layers import LayerShip, LayerSmoke, LayerShot, LayerTorpedo
from PIL import Image
from itertools import zip_longest
from imageio_ffmpeg import write_frames
from concurrent.futures import ThreadPoolExecutor


class Renderer(RendererBase):
    def __init__(self, replay_data: ReplayData):
        """Orchestrates the rendering process.

        Args:
            replay_data (ReplayData): Replay data.
        """
        self._replay_data: ReplayData = replay_data
        self._res: str = f"{__package__}.resources"
        # MAP INFO
        self._minimap_image: Optional[Image.Image] = None
        self._minimap_size: int = 0
        self._space_size: int = 0
        self._scaling: float = 0.0

    def start(self):
        """Starts the rendering process"""
        self._load_map()
        assert self._minimap_image

        layer_ship = LayerShip(
            self._replay_data.events,
            self._scaling,
            self._replay_data.player_info,
        )
        layer_smoke = LayerSmoke(self._replay_data.events, self._scaling)
        layer_shot = LayerShot(
            self._replay_data.events,
            self._scaling,
            self._replay_data.player_info,
        )
        layer_torpedo = LayerTorpedo(
            self._replay_data.events,
            self._scaling,
            self._replay_data.player_info,
        )

        video_writer = write_frames(
            path="hm.mp4",
            fps=30,
            quality=9,
            pix_fmt_in="rgba",
            macro_block_size=19,
            size=(760, 760),
        )
        video_writer.send(None)

        for game_time, event in self._replay_data.events.items():
            minimap_img = self._minimap_image.copy()

            executors = []

            with ThreadPoolExecutor(max_workers=3) as tpe:
                executors.append(
                    tpe.submit(layer_torpedo.generator, game_time)
                )
                executors.append(tpe.submit(layer_shot.generator, game_time))
                executors.append(tpe.submit(layer_smoke.generator, game_time))
                executors.append(tpe.submit(layer_ship.generator, game_time))

            for executor in executors:
                if result := executor.result():
                    minimap_img = Image.alpha_composite(minimap_img, result)

            # if image_torpedoes := layer_torpedo.generator(game_time):
            #     minimap_img = Image.alpha_composite(
            #         minimap_img, image_torpedoes
            #     )

            # if gen_shot := layer_shot.generator(game_time):
            #     minimap_img = Image.alpha_composite(minimap_img, gen_shot)

            # if gen_smoke := layer_smoke.generator(game_time):
            #     minimap_img = Image.alpha_composite(minimap_img, gen_smoke)

            # if gen_ship := layer_ship.generator(game_time):
            #     minimap_img = Image.alpha_composite(minimap_img, gen_ship)

            video_writer.send(minimap_img.tobytes())
        video_writer.close()

    def _load_map(self):
        """Loads and prepares the map."""
        with open_text(f"{self._res}.spaces", "manifest.json") as reader:
            manifest = json.load(reader)
            self._minimap_size, self._space_size, self._scaling = manifest[
                self._replay_data.game_map
            ]

        map_res = f"{self._res}.spaces.{self._replay_data.game_map}"
        map_land = load_image(map_res, "minimap.png")
        map_water = load_image(map_res, "minimap_water.png")
        map_water = Image.alpha_composite(map_water, draw_grid())
        self._minimap_image = Image.alpha_composite(map_water, map_land)
        # draw = ImageDraw.Draw(self._minimap_image)
        # draw.ellipse(xy=[(2, 760 / 2), (2, 760 / 2 + 2)], fill="white")
