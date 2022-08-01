import json

from typing import Optional
from importlib.resources import open_text
from importlib import import_module

from renderer.data import ReplayData
from renderer.utils import draw_grid, LOGGER
from renderer.resman import ResourceManager
from renderer.exceptions import MapLoadError, MapManifestLoadError
from PIL import Image, ImageDraw
from imageio_ffmpeg import write_frames


class Renderer:
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

        (
            layer_ship,
            layer_shot,
            layer_torpedo,
            layer_smoke,
        ) = self._check_versioned_layers()

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
        """Loads the map.

        Raises:
            MapLoadError: Raised when an error occurs when loading a map
            resource.
            MapManifestLoadError: Raised when an error occurs when loading maps
            manifest.
        """
        LOGGER.info("Looking for versioned map resource...")
        map_res = self._load_map_manifest()

        try:
            map_land = self.resman.load_image(map_res, "minimap.png")
            map_water = self.resman.load_image(map_res, "minimap_water.png")
            map_water = Image.alpha_composite(map_water, draw_grid())
            self.minimap_image = Image.alpha_composite(map_water, map_land)
        except (FileNotFoundError, ModuleNotFoundError) as e:
            raise MapLoadError from e

    def _load_map_manifest(self) -> str:
        """Loads the map's metadata and checks its values.

        Raises:
            MapManifestLoadError: Raised when there's an error when loading the
            manifest file or the map's metadata is unsuitable.

        Returns:
            str: Package on where the map resources will be loaded.
        """
        version = self.replay_data.game_version
        pkg = f"{__package__}.versions.{version}.resources.spaces"
        map_default = f"{self.res}.spaces.{self.replay_data.game_map}"
        map_versioned = f"{pkg}.{self.replay_data.game_map}"

        try:
            try:
                with open_text(pkg, "manifest.json") as mr:
                    manifest = json.load(mr)[self.replay_data.game_map]
                    self.minimap_size, self.space_size, self.scaling = manifest
                LOGGER.info(
                    "Versioned map resource found. Loading that instead..."
                )
                map_res = map_versioned
            except (FileNotFoundError, KeyError):
                with open_text(
                    f"{self.res}.spaces", "manifest.json"
                ) as reader:
                    manifest = json.load(reader)
                    (
                        self.minimap_size,
                        self.space_size,
                        self.scaling,
                    ) = manifest[self.replay_data.game_map]
                LOGGER.info(
                    "No versioned map resource found. Loading default..."
                )
                map_res = map_default

            assert isinstance(self.minimap_size, int)
            assert isinstance(self.space_size, int)
            assert isinstance(self.scaling, float)
            assert 0 < self.space_size <= 1600
            assert 760 == self.minimap_size
        except Exception as e:
            raise MapManifestLoadError from e
        else:
            return map_res

    def _check_versioned_layers(self):
        versioned_layers_pkg = (
            f"{__package__}.versions.{self.replay_data.game_version}"
        )

        layers = ["LayerShip", "LayerShot", "LayerTorpedo", "LayerSmoke"]
        init_layers = []

        LOGGER.info("Looking for versioned layers")

        for layer in layers:
            try:
                mod = import_module(".layers", versioned_layers_pkg)
                m_layer = getattr(mod, layer)
                LOGGER.info(f"Versioned {layer} found. Using that instead.")
            except (ModuleNotFoundError, AttributeError):
                mod = import_module(".layers", __package__)
                m_layer = getattr(mod, f"{layer}Base")
            init_layers.append(m_layer(self))
        return init_layers
