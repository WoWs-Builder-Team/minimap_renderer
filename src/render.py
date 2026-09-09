import argparse
import json
from pathlib import Path
import sys
from renderer.render import (
    ENCODER_MODES,
    INTERPOLATION_MODES,
    VIDEO_CODECS,
    Renderer,
)
from renderer.report import generate_battle_report
from replay_parser import ReplayParser
from renderer.utils import LOGGER


def resolution(value: str) -> tuple[int, int]:
    try:
        width, height = map(int, value.lower().split("x", maxsplit=1))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "resolution must use WIDTHxHEIGHT, for example 1920x1200"
        ) from exc

    if width <= 0 or height <= 0 or width % 2 or height % 2:
        raise argparse.ArgumentTypeError(
            "resolution width and height must be positive even numbers"
        )
    return width, height


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", type=str, required=True)
    parser.add_argument(
        "--fps", type=int, default=60, help="output frame rate (default: 60)"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=15,
        help="timelapse playback speed (default: 15x)",
    )
    parser.add_argument(
        "--resolution",
        type=resolution,
        default=(1920, 1200),
        metavar="WIDTHxHEIGHT",
        help="output resolution (default: 1920x1200)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        choices=range(1, 11),
        default=8,
        metavar="1-10",
        help="encoding quality (default: 8)",
    )
    parser.add_argument(
        "--interpolation",
        choices=INTERPOLATION_MODES,
        default="native",
        help="frame interpolation mode (default: native)",
    )
    parser.add_argument(
        "--codec",
        choices=VIDEO_CODECS,
        default="h264",
        help="video codec (default: h264)",
    )
    parser.add_argument(
        "--encoder",
        choices=ENCODER_MODES,
        default="auto",
        help="video encoder; auto probes hardware and falls back to CPU "
        "(default: auto)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="disable automatic battle report infographic generation",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="generate 2.4K battle report infographic only (skips timelapse video rendering)",
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default=None,
        help="custom output path for battle report infographic image",
    )
    namespace = parser.parse_args()
    if namespace.fps <= 0:
        parser.error("--fps must be greater than 0")
    if namespace.speed <= 0:
        parser.error("--speed must be greater than 0")
    path = Path(namespace.replay)
    report_output_path = namespace.report_path or str(path.parent.joinpath(f"{path.stem}-report.png"))

    if namespace.report_only:
        LOGGER.info("Generating 2.4K Ultra-HD battle report (--report-only)...")
        generate_battle_report(namespace.replay, report_output_path)
        LOGGER.info(f"Battle report saved to: {report_output_path}")
        LOGGER.info("Done.")
        sys.exit(0)

    video_path = path.parent.joinpath(f"{path.stem}.mp4")
    with open(namespace.replay, "rb") as f:
        LOGGER.info("Parsing the replay file...")
        replay_info = ReplayParser(
            f, strict=True, raw_data_output=False
        ).get_info()
        LOGGER.info(
            "Replay has version "
            f"{replay_info['open']['clientVersionFromExe']}"
        )
        LOGGER.info("Rendering the replay file...")
        renderer = Renderer(
            replay_info["hidden"]["replay_data"],
            logs=True,
            enable_chat=True,
            use_tqdm=True,
        )
        with open(path.parent.joinpath(f"{path.stem}-builds.json"), "w") as fp:
            json.dump(renderer.get_player_build(), fp, indent=4)
        renderer.start(
            str(video_path),
            fps=namespace.fps,
            speed=namespace.speed,
            resolution=namespace.resolution,
            quality=namespace.quality,
            interpolation=namespace.interpolation,
            encoder=namespace.encoder,
            video_codec=namespace.codec,
        )
        LOGGER.info(f"The video file is at: {str(video_path)}")

    if not namespace.no_report:
        LOGGER.info("Generating 2.4K Ultra-HD battle report...")
        try:
            generate_battle_report(namespace.replay, report_output_path)
            LOGGER.info(f"Battle report saved to: {report_output_path}")
        except Exception as e:
            LOGGER.warning(f"Failed to generate battle report: {e}")

    LOGGER.info("Done.")
