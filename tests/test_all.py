import pytest
import pickle

from renderer.render import Renderer
from src.replay_parser import ReplayParser


@pytest.mark.parametrize(
    "file",
    [
        "replays/116.wowsreplay",
        "replays/117.wowsreplay",
        "replays/118.wowsreplay",
        "replays/119.wowsreplay",
    ],
)
def test_all(file):
    with open(file, "rb") as f:
        replay_info = ReplayParser(
            f, strict=True, raw_data_output=False
        ).get_info()

        renderer = Renderer(
            replay_info["hidden"]["replay_data"],
            logs=True,
            enable_chat=True,
            use_tqdm=True,
        )
        renderer.get_player_build()
        renderer.start("minimap.mp4")
