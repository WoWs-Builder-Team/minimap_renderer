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
        "replays/1110.wowsreplay",
        "replays/1111.wowsreplay",
        "replays/120.wowsreplay",
        "replays/121.wowsreplay",
        "replays/122.wowsreplay",
        "replays/123.wowsreplay",
        "replays/124.wowsreplay",
        "replays/125.wowsreplay",
        "replays/126.wowsreplay",
        "replays/127.wowsreplay",
        "replays/128.wowsreplay",
        "replays/129.wowsreplay",
        "replays/1210.wowsreplay",
        "replays/1211.wowsreplay",
        "replays/130.wowsreplay",
        "replays/131.wowsreplay",
        "replays/132.wowsreplay",
        "replays/133.wowsreplay",
        "replays/134.wowsreplay",
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
