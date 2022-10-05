import os

from os import path
from src.replay_parser import ReplayParser
from renderer.data import ReplayData
from renderer.render import RenderDual


DIR = os.path.dirname(__file__)
REPLAY_DIR = path.join(DIR, "replays")


if __name__ == "__main__":
    with (
        open(path.join(REPLAY_DIR, "team1.wowsreplay"), "rb") as gt,
        open(path.join(REPLAY_DIR, "team2.wowsreplay"), "rb") as rt,
    ):
        g_replay_info = ReplayParser(gt, True).get_info()
        g_replay_data: ReplayData = g_replay_info["hidden"]["replay_data"]

        r_replay_info = ReplayParser(rt, True).get_info()
        r_replay_data: ReplayData = r_replay_info["hidden"]["replay_data"]

        RenderDual(
            g_replay_data, r_replay_data, green_tag="Alpha", red_tag="Bravo"
        ).start("minimap_dual.mp4")
