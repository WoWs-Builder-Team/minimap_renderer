"""
World of Warships Replay Battle Report Infographic Generator CLI Tool.
Directly invokes `renderer.report.generate_battle_report`.
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure src is on sys.path
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from renderer.report import generate_battle_report, parse_replay_report, render_battle_report_card


def main():
    parser = argparse.ArgumentParser(description="World of Warships 2.4K Battle Report Infographic Generator")
    parser.add_argument("replay", help="Path to .wowsreplay file")
    parser.add_argument("-o", "--output", default=None, help="Output path for -report.png image")
    args = parser.parse_args()

    replay_path = os.path.abspath(args.replay)
    out_path = os.path.abspath(args.output) if args.output else None

    print(f"Parsing replay and generating battle report: {replay_path} ...")
    result = generate_battle_report(replay_path, out_path)
    print(f"Battle report successfully created at: {result}")


if __name__ == "__main__":
    main()
