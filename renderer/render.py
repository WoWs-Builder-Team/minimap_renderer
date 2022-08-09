from json import JSONDecodeError
from typing import Optional, Union
from importlib import import_module
from renderer.base import LayerBase

from renderer.const import OPERATIONS, LAYERS
from renderer.data import ReplayData
from renderer.utils import draw_grid, LOGGER
from renderer.resman import ResourceManager
from renderer.exceptions import MapLoadError
from PIL import Image, ImageDraw
from imageio_ffmpeg import write_frames
from tqdm import tqdm

Number = Union[int, float]


class Renderer:
    def __init__(self, replay_data: ReplayData, anon: bool = False):
        """Orchestrates the rendering process.

        Args:
            replay_data (ReplayData): Replay data.
        """
        self.replay_data: ReplayData = replay_data
        self.res: str = f"{__package__}.resources"
        self.resman = ResourceManager(replay_data.game_version)
        # MAP INFO
        self.minimap_image: Optional[Image.Image] = None
        self.minimap_bg: Optional[Image.Image] = None
        self.minimap_size: int = 0
        self.space_size: int = 0
        self.scaling: float = 0.0
        self.is_operations = False
        self._anon = anon
        self.usernames: dict[int, str] = {}

    def _create_usernames(self):
        for i, (pid, pi) in enumerate(self.replay_data.player_info.items(), 1):
            name = f"PLAYER_{i}"
            self.usernames[pid] = name

    def start(self, path: str, fps: int = 20, enable_chat=True):
        """Starts the rendering process"""
        self._load_map()

        assert self.minimap_image
        assert self.minimap_bg

        layer_ship = self._load_base_or_versioned("LayerShip")
        layer_shot = self._load_base_or_versioned("LayerShot")
        layer_torpedo = self._load_base_or_versioned("LayerTorpedo")
        layer_smoke = self._load_base_or_versioned("LayerSmoke")
        layer_plane = self._load_base_or_versioned("LayerPlane")
        layer_ward = self._load_base_or_versioned("LayerWard")
        layer_capture = self._load_base_or_versioned("LayerCapture")
        layer_health = self._load_base_or_versioned("LayerHealth")
        layer_score = self._load_base_or_versioned("LayerScore")
        layer_counter = self._load_base_or_versioned("LayerCounter")
        layer_frag = self._load_base_or_versioned("LayerFrag")
        layer_timer = self._load_base_or_versioned("LayerTimer")
        layer_ribbon = self._load_base_or_versioned("LayerRibbon")
        layer_chat = self._load_base_or_versioned("LayerChat")

        video_writer = write_frames(
            path=path,
            fps=fps,
            quality=7,
            pix_fmt_in="rgba",
            macro_block_size=17,
            size=self.minimap_bg.size,
        )
        video_writer.send(None)

        self._draw_header(self.minimap_bg)

        for game_time in tqdm(self.replay_data.events.keys()):
            minimap_img = self.minimap_image.copy()
            minimap_bg = self.minimap_bg.copy()

            draw = ImageDraw.Draw(minimap_img)
            layer_capture.draw(game_time, minimap_img)
            layer_ward.draw(game_time, minimap_img)
            layer_shot.draw(game_time, draw)
            layer_torpedo.draw(game_time, draw)
            layer_ship.draw(game_time, minimap_img)
            layer_smoke.draw(game_time, minimap_img)
            layer_plane.draw(game_time, minimap_img)

            layer_health.draw(game_time, minimap_bg)
            layer_score.draw(game_time, minimap_bg)
            layer_counter.draw(game_time, minimap_bg)
            layer_frag.draw(game_time, minimap_bg)
            layer_timer.draw(game_time, minimap_bg)
            layer_ribbon.draw(game_time, minimap_bg)
            if enable_chat:
                layer_chat.draw(game_time, minimap_bg)

            minimap_bg.paste(minimap_img, (40, 90))  # 40, 40 w/o logs
            video_writer.send(minimap_bg.tobytes())
        video_writer.close()

    def _draw_header(self, image: Image.Image):
        draw = ImageDraw.Draw(image)

        logo = self.resman.load_image("logo.png")
        image.paste(logo, (840, 25), logo)

        font_large = self.resman.load_font("warhelios_bold.ttf", size=35)
        draw.text((945, 30), "Minimap Renderer", "white", font_large)

        font_large = self.resman.load_font("warhelios_bold.ttf", size=16)
        draw.text(
            (945, 75),
            "https://github.com/WoWs-Builder-Team",
            "white",
            font_large,
        )

    def _load_map(self):
        """Loads the map.

        Raises:
            MapLoadError: Raised when an error occurs when loading a map
            resource.
            MapManifestLoadError: Raised when an error occurs when loading maps
            manifest.
        """
        self._load_map_manifest()
        path = f"spaces.{self.replay_data.game_map}"

        try:
            map_legends = self.resman.load_image("minimap_grid_legends.png")
            map_land = self.resman.load_image("minimap.png", path=path)
            map_water = self.resman.load_image("minimap_water.png", path=path)
            self.minimap_bg = map_water.copy().resize((1360, 850))  # 800, 800
            self.minimap_bg.paste(
                map_legends,
                (
                    0,
                    50,
                ),
                mask=map_legends,
            )  # no pos.

            map_water = Image.alpha_composite(map_water, draw_grid())
            self.minimap_image = Image.alpha_composite(map_water, map_land)
        except (FileNotFoundError, ModuleNotFoundError) as e:
            raise MapLoadError from e

    def _load_map_manifest(self):
        """Loads the map's metadata and checks its values.

        Raises:
            MapManifestLoadError: Raised when there's an error when loading the
            manifest file or the map's metadata is unsuitable.

        Returns:
            str: Package on where the map resources will be loaded.
        """
        try:
            manifest = self.resman.load_json("manifest.json", "spaces")
            manifest = manifest[self.replay_data.game_map]
        except (KeyError, JSONDecodeError):
            manifest = self.resman.load_json("manifest.json", "spaces", True)
            manifest = manifest[self.replay_data.game_map]

        self.minimap_size, self.space_size, self.scaling = manifest
        assert isinstance(self.minimap_size, int)
        assert isinstance(self.space_size, int)
        assert isinstance(self.scaling, float)
        assert 0 < self.space_size <= 1600
        assert 760 == self.minimap_size

    def get_scaled(
        self, xy: tuple[Number, Number], flip_y=True
    ) -> tuple[int, int]:
        """Scales a coordinate properly.

        Args:
            xy (tuple[Number, Number]): Coordinate.
            flip_y (bool, optional): Flips the y component. Defaults to True.

        Returns:
            tuple[int, int]: Scaled coordinated.
        """
        x, y = xy

        if flip_y:
            y = -y

        x = round(x * self.scaling + self.minimap_size / 2)
        y = round(y * self.scaling + self.minimap_size / 2)
        return x, y

    def get_scaled_r(self, r: Number):
        return r * self.scaling

    def _load_base_or_versioned(self, layer_name: str) -> LayerBase:
        assert layer_name in LAYERS
        versioned_layers_pkg = (
            f"{__package__}.versions.{self.replay_data.game_version}"
        )
        try:
            mod = import_module(".layers", versioned_layers_pkg)
            m_layer = getattr(mod, layer_name)
            LOGGER.info(f"Versioned {layer_name} found. Using that instead.")
        except (ModuleNotFoundError, AttributeError):
            mod = import_module(".layers", __package__)
            m_layer = getattr(mod, f"{layer_name}Base")
        return m_layer(self)
