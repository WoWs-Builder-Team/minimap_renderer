from pathlib import Path
from renderer.render import Renderer
from replay_parser import ReplayParser
from renderer.utils import LOGGER
from interpolation.Interpolation import Interpolator

def run(pathStr):
    fps=60
    speed_scale=20.0
    path = Path(pathStr)
    video_path = path.parent.joinpath(f"{path.stem}.mp4")
    with open(path, "rb") as f:
        LOGGER.info("Parsing the replay file...")
        replay_info = ReplayParser(
            f, strict=True, raw_data_output=False
        ).get_info()
        LOGGER.info("before interpolation: replay_info length: %d", len(replay_info["hidden"]["replay_data"].events))
        replay_info["hidden"]["replay_data"]=Interpolator().interpolate(
            replay_info["hidden"]["replay_data"],
            fpsTarget=fps,
            speedScale=speed_scale
        )
        LOGGER.info("after interpolation: replay_info length: %d", len(replay_info["hidden"]["replay_data"].events))
        LOGGER.info("Rendering the replay file...")
        renderer = Renderer(
            replay_info["hidden"]["replay_data"],
            logs=True,
            enable_chat=True,
            use_tqdm=True,
            fps=fps,
            speed_scale=speed_scale
        )
        renderer.start(str(video_path))
        LOGGER.info(f"The video file is at: {str(video_path)}")
        LOGGER.info("Done.")

if __name__ == "__main__":
    # run("/home/reinwd/replays/20231014/20231014_191413_PZSD110-Hsiang-Yang_54_Faroe.wowsreplay")
    # run("/home/reinwd/replays/20231014/20231015_203924_PZSD110-Hsiang-Yang_53_Shoreside.wowsreplay")
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", type=str, required=True)
    namespace = parser.parse_args()
    run(namespace.replay)