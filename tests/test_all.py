import pytest
import pickle

from renderer.render import Renderer
from replay_parser import ReplayParser


@pytest.mark.parametrize(
    "file", ["replays/116.wowsreplay", "replays/117.wowsreplay"]
)
def test_parser(file):
    with open(file, "rb") as bio:
        ReplayParser(bio, strict=True).get_info()["hidden"]["replay_data"]


@pytest.mark.parametrize("file", ["replays/116.dat", "replays/117.dat"])
def test_t_logs_t_chat(file):
    with open(file, "rb") as f:
        Renderer(pickle.load(f), logs=True, enable_chat=True).start(
            "minimap.mp4"
        )


@pytest.mark.parametrize("file", ["replays/116.dat", "replays/117.dat"])
def test_t_logs_f_chat(file):
    with open(file, "rb") as f:
        Renderer(pickle.load(f), logs=True, enable_chat=False).start(
            "minimap.mp4"
        )


@pytest.mark.parametrize("file", ["replays/116.dat", "replays/117.dat"])
def test_t_logs_t_chat_t_anon(file):
    with open(file, "rb") as f:
        Renderer(pickle.load(f), logs=True, enable_chat=True, anon=True).start(
            "minimap.mp4"
        )


@pytest.mark.parametrize("file", ["replays/116.dat", "replays/117.dat"])
def test_f_logs_t_tracers(file):
    with open(file, "rb") as f:
        Renderer(pickle.load(f), logs=False, team_tracers=True).start(
            "minimap.mp4"
        )
