from json import JSONDecodeError
from typing import Any, Callable, Optional, Type, Union
from importlib import import_module
from renderer.base import LayerBase

from renderer.const import LAYERS
from renderer.data import ReplayData
from renderer.utils import draw_grid, LOGGER
from renderer.resman import ResourceManager
from renderer.exceptions import MapLoadError
from PIL import Image, ImageDraw
from imageio_ffmpeg import write_frames
from tqdm import tqdm

Number = Union[int, float]


class RenderDual:
    def __init__(
        self,
        green_replay_data: ReplayData,
        red_replay_data: ReplayData,
        green_tag: Optional[str] = None,
        red_tag: Optional[str] = None,
        team_tracers: bool = False,
        use_tqdm: bool = True,
    ):
        self.replay_g: ReplayData = green_replay_data
        self.replay_r: ReplayData = red_replay_data
        # assert self.replay_g.game_arena_id == self.replay_r.game_arena_id
        assert self.replay_g.game_version == self.replay_r.game_version
        self.resman = ResourceManager(self.replay_g.game_version)
        self.minimap_image: Optional[Image.Image] = None
        self.minimap_bg: Optional[Image.Image] = None
        self.minimap_size: int = 0
        self.space_size: int = 0
        self.scaling: float = 0.0
        self.dual_mode: bool = True
        self.green_tag = green_tag
        self.red_tag = red_tag
        self.team_tracers = team_tracers
        self.bg_color: tuple[int, int, int] = (0, 0, 0)
        self.use_tqdm = use_tqdm

    def start(
        self,
        path: str,
        fps: int = 20,
        quality: int = 7,
        progress_cb: Optional[Callable[[float], Any]] = None,
    ):
        self._load_map()

        assert self.minimap_image
        assert self.minimap_bg

        # green
        g_ship = self._load_base_or_versioned("LayerShip")(
            self, self.replay_g, "green"
        )
        g_shot = self._load_base_or_versioned("LayerShot")(
            self, self.replay_g, "green"
        )
        g_torpedo = self._load_base_or_versioned("LayerTorpedo")(
            self, self.replay_g, "green"
        )
        g_plane = self._load_base_or_versioned("LayerPlane")(
            self, self.replay_g, "green"
        )
        g_ward = self._load_base_or_versioned("LayerWard")(
            self, self.replay_g, "green"
        )

        g_smoke = self._load_base_or_versioned("LayerSmoke")(
            self, self.replay_g
        )
        g_capture = self._load_base_or_versioned("LayerCapture")(
            self, self.replay_g
        )
        g_score = self._load_base_or_versioned("LayerScore")(
            self, self.replay_g, green_tag=self.green_tag, red_tag=self.red_tag
        )
        g_timer = self._load_base_or_versioned("LayerTimer")(
            self, self.replay_g
        )

        # red
        r_ship = self._load_base_or_versioned("LayerShip")(
            self, self.replay_r, "red"
        )
        r_shot = self._load_base_or_versioned("LayerShot")(
            self, self.replay_r, "red"
        )
        r_torpedo = self._load_base_or_versioned("LayerTorpedo")(
            self, self.replay_r, "red"
        )
        r_plane = self._load_base_or_versioned("LayerPlane")(
            self, self.replay_r, "red"
        )
        r_ward = self._load_base_or_versioned("LayerWard")(
            self, self.replay_r, "red"
        )

        video_writer = write_frames(
            path=path,
            fps=fps,
            quality=quality,
            pix_fmt_in="rgba",
            macro_block_size=10,
            size=self.minimap_bg.size,
            output_params=[
                "-profile:v",
                "high",
                "-movflags",
                "+faststart",
                "-tune",
                "animation",
            ],
        )
        video_writer.send(None)

        if self.use_tqdm:
            prog = tqdm(
                set(self.replay_g.events).intersection(self.replay_r.events)
            )
        else:
            prog = set(self.replay_g.events).intersection(self.replay_r.events)

        total = len(prog)
        last_per = 0.0

        for idx, i in enumerate(prog):
            if progress_cb:
                per = round((idx + 1) / total, 1)
                if per > last_per:
                    last_per = per
                    progress_cb(per)

            minimap_img = self.minimap_image.copy()
            minimap_bg = self.minimap_bg.copy()
            draw = ImageDraw.Draw(minimap_img)

            g_capture.draw(i, minimap_img)
            g_smoke.draw(i, minimap_img)
            g_score.draw(i, minimap_bg)
            g_timer.draw(i, minimap_bg)

            g_ward.draw(i, minimap_img)
            r_ward.draw(i, minimap_img)

            g_torpedo.draw(i, draw)
            r_torpedo.draw(i, draw)

            g_shot.draw(i, draw)
            r_shot.draw(i, draw)

            g_ship.draw(i, minimap_img)
            r_ship.draw(i, minimap_img)

            g_plane.draw(i, minimap_img)
            r_plane.draw(i, minimap_img)

            minimap_bg.paste(minimap_img, (40, 90))
            video_writer.send(minimap_bg.tobytes())
        video_writer.close()

    def _load_map(self):
        """Loads the map.

        Raises:
            MapLoadError: Raised when an error occurs when loading a map
            resource.
            MapManifestLoadError: Raised when an error occurs when loading maps
            manifest.
        """
        self._load_map_manifest()
        path = f"spaces.{self.replay_g.game_map}"

        try:
            map_legends = self.resman.load_image("minimap_grid_legends.png")
            map_land = self.resman.load_image("minimap.png", path=path)
            map_water = self.resman.load_image("minimap_water.png", path=path)
            self.minimap_bg = map_water.copy().resize((800, 850))

            self.minimap_bg.paste(
                map_legends,
                (
                    0,
                    50,
                ),
                mask=map_legends,
            )
            self.bg_color = map_water.getpixel((10, 10))

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
            manifest = manifest[self.replay_g.game_map]
        except (KeyError, JSONDecodeError):
            manifest = self.resman.load_json("manifest.json", "spaces", True)
            manifest = manifest[self.replay_g.game_map]

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

    def _load_base_or_versioned(self, layer_name: str) -> Type[LayerBase]:
        assert layer_name in LAYERS
        versioned_layers_pkg = (
            f"{__package__}.versions.{self.replay_g.game_version}"
        )
        try:
            mod = import_module(".layers", versioned_layers_pkg)
            m_layer = getattr(mod, layer_name)
            LOGGER.info(f"Versioned {layer_name} found. Using that instead.")
        except (ModuleNotFoundError, AttributeError):
            mod = import_module(".layers", __package__)
            m_layer = getattr(mod, f"{layer_name}Base")
        return m_layer


class Renderer:
    def __init__(
        self,
        replay_data: ReplayData,
        logs: bool = True,
        anon: bool = False,
        enable_chat: bool = True,
        team_tracers: bool = False,
        use_tqdm: bool = False,
    ):
        """Orchestrates the rendering process.

        Args:
            replay_data (ReplayData): Replay data.
        """
        self.replay_data: ReplayData = replay_data
        self.resman = ResourceManager(replay_data.game_version)
        # MAP INFO
        self.minimap_image: Optional[Image.Image] = None
        self.minimap_bg: Optional[Image.Image] = None
        self.logs: bool = logs
        self.minimap_size: int = 0
        self.space_size: int = 0
        self.scaling: float = 0.0
        self.is_operations: bool = False
        self.anon: bool = anon
        self.enable_chat: bool = enable_chat
        self.team_tracers: bool = team_tracers
        self.usernames: dict[int, str] = {}
        self.dual_mode: bool = False
        self.bg_color: tuple[int, int, int] = (0, 0, 0)
        self.use_tqdm = use_tqdm

        if self.anon:
            for i, (pid, pi) in enumerate(
                self.replay_data.player_info.items(), 1
            ):
                name = f"Player {i}"
                self.usernames[pid] = name

    def _check_if_operations(self):
        bts = self.resman.load_json("battle_types.json")
        bt = bts[self.replay_data.game_battle_type]

        if bt["scenario"][:2].startswith("OP"):
            self.is_operations = True

    def start(
        self,
        path: str,
        fps: int = 20,
        quality: int = 7,
        progress_cb: Optional[Callable[[float], Any]] = None,
    ):
        """Starts the rendering process"""
        self._check_if_operations()
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

        m_block = 10 if self.logs else 17

        video_writer = write_frames(
            path=path,
            fps=fps,
            quality=quality,
            pix_fmt_in="rgba",
            macro_block_size=m_block,
            size=self.minimap_bg.size,
            output_params=[
                "-profile:v",
                "high",
                "-movflags",
                "+faststart",
                "-tune",
                "animation",
            ],
        )
        video_writer.send(None)

        self._draw_header(self.minimap_bg)

        last_key = list(self.replay_data.events)[-1]

        if self.use_tqdm:
            prog = tqdm(self.replay_data.events.keys())
        else:
            prog = self.replay_data.events.keys()

        total = len(prog)
        last_per = 0.0

        for idx, game_time in enumerate(prog):
            if progress_cb:
                per = round((idx + 1) / total, 1)
                if per > last_per:
                    last_per = per
                    progress_cb(per)

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

            layer_timer.draw(game_time, minimap_bg)
            layer_score.draw(game_time, minimap_bg)

            if self.logs:
                layer_health.draw(game_time, minimap_bg)
                layer_counter.draw(game_time, minimap_bg)
                layer_frag.draw(game_time, minimap_bg)

                layer_ribbon.draw(game_time, minimap_bg)
                if self.enable_chat:
                    layer_chat.draw(game_time, minimap_bg)

            if game_time == last_key:
                img_win = Image.new("RGBA", self.minimap_image.size)
                drw_win = ImageDraw.Draw(img_win)
                font = self.resman.load_font("warhelios_bold.ttf", size=36)
                player = self.replay_data.player_info[
                    self.replay_data.owner_id
                ]

                team_id = self.replay_data.game_result.team_id

                match team_id:
                    case a if a == player.team_id and a != -1:
                        text = "YOUR TEAM WON"
                    case a if a != player.team_id and a != -1:
                        text = "THE ENEMY TEAM WON"
                    case _:
                        text = "???"

                tw, th = map(lambda i: i / 2, font.getsize(text))
                mid_x, mid_y = map(lambda i: i / 2, minimap_img.size)
                offset_y = 4
                px, py = mid_x - tw, mid_y - th - offset_y

                for i in range(3 * fps):
                    per = min(1, i / (1.5 * fps))
                    drw_win.text(
                        (px, py),
                        text=text,
                        font=font,
                        fill=(255, 255, 255, round(255 * per)),
                        stroke_width=4,
                        stroke_fill=(*self.bg_color[:3], round(255 * per)),
                    )

                    minimap_img = Image.alpha_composite(minimap_img, img_win)
                    minimap_bg.paste(minimap_img, (40, 90))
                    video_writer.send(minimap_bg.tobytes())
            else:
                minimap_bg.paste(minimap_img, (40, 90))
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

        if self.is_operations:
            map_name = f"s{self.replay_data.game_map}"
        else:
            map_name = self.replay_data.game_map

        self._load_map_manifest()
        path = f"spaces.{map_name}"

        try:
            map_legends = self.resman.load_image("minimap_grid_legends.png")
            map_land = self.resman.load_image("minimap.png", path=path)
            map_water = self.resman.load_image("minimap_water.png", path=path)
            if not self.logs:
                self.minimap_bg = map_water.copy().resize((800, 850))
            else:
                self.minimap_bg = map_water.copy().resize((1360, 850))
            self.minimap_bg.paste(
                map_legends,
                (
                    0,
                    50,
                ),
                mask=map_legends,
            )  # no pos.
            self.bg_color = map_water.getpixel((10, 10))
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
        if self.is_operations:
            map_name = f"s{self.replay_data.game_map}"
        else:
            map_name = self.replay_data.game_map

        try:
            manifest = self.resman.load_json("manifest.json", "spaces")
            manifest = manifest[map_name]
        except (KeyError, JSONDecodeError):
            manifest = self.resman.load_json("manifest.json", "spaces", True)
            manifest = manifest[map_name]

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
