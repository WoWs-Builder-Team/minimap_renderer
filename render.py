from pathlib import Path
from renderer.render import Renderer
from replay_parser import ReplayParser


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", type=str, required=True)
    namespace = parser.parse_args()
    filename = Path(namespace.replay).stem
    with open(namespace.replay, "rb") as f:
        replay_info = ReplayParser(
            f, strict=True, raw_data_output=False
        ).get_info()
        
        renderer = Renderer(
            replay_info["hidden"]["replay_data"],
            logs=True,
            enable_chat=True,
            use_tqdm=True,
        )
        renderer.start(f"{filename}.mp4")
