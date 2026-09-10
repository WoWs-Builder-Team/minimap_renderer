import os
import pytest
from renderer.report import generate_battle_report, parse_replay_report

DEFAULT_REPLAY_PATH = os.path.join(os.path.dirname(__file__), "..", "replays", "1580.wowsreplay")
CUSTOM_REPLAY_PATH = r"F:\[工具]\minimap_renderer\20260907_123622_PWSB010-Thor_58_RidgeNew.wowsreplay"
REPLAY_PATH = CUSTOM_REPLAY_PATH if os.path.exists(CUSTOM_REPLAY_PATH) else DEFAULT_REPLAY_PATH


def test_parse_replay_report():
    if not os.path.exists(REPLAY_PATH):
        pytest.skip("Test replay file not found")
    data = parse_replay_report(REPLAY_PATH)
    assert data["has_post_battle"] is True
    assert "owner" in data
    assert data["owner"]["name"] != ""
    assert len(data["players"]) > 0


def test_generate_battle_report(tmp_path):
    if not os.path.exists(REPLAY_PATH):
        pytest.skip("Test replay file not found")
    out_file = str(tmp_path / "test_report.png")
    result = generate_battle_report(REPLAY_PATH, out_file)
    assert os.path.exists(result)
    assert os.path.getsize(result) > 100000
