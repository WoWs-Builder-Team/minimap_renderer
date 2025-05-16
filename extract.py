"""
This script should be placed in the root of a WoWS installation.
It will generate and populate res_extract.

Make sure you have the unpacker:
https://forum.worldofwarships.eu/topic/113847-all-wows-unpack-tool-unpack-game-client-resources/
"""

import argparse
import os
import shutil
import subprocess

OUTPUT_NAME = "res_extract"
UNPACK_LIST = (
    "content/GameParams.data",
    "scripts/*",
    "spaces/*/minimap*.png",
    "spaces/*/space.settings",
    "gui/achievements/*",
    "gui/ribbons/*",
    "gui/ship_bars/*",
    "gui/ships_silhouettes/*",
    "gui/consumables/consumable_*_*.png",
    "gui/ship_bars/*",
    "gui/service_kit/building_icons/*",
    "gui/battle_hud/icon_frag/*",
)
EXCLUDE_LIST = (
    "gui/consumables/consumable_*_*_empty.png",
)


def main(bin_num):
    bin_path = fr"bin\{bin_num}"
    idx_path = fr"{bin_path}\idx"
    pkg_path = r"..\..\..\res_packages"
    include = [i for pattern in UNPACK_LIST for i in ("-I", pattern)]
    exclude = [i for pattern in EXCLUDE_LIST for i in ("-X", pattern)]

    subprocess.run(["wowsunpack.exe", "-x", idx_path,
                    "-p", pkg_path,
                    "-o", OUTPUT_NAME,
                    *include, *exclude])

    texts_src = fr"{bin_path}\res\texts"
    texts_dest = fr"{OUTPUT_NAME}\texts"
    shutil.copytree(texts_src, texts_dest)

    print("Extraction complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extracts game resources.")
    parser.add_argument("--bin",
                        default=max(os.listdir("bin/")),
                        help="The game version to use.")
    args = parser.parse_args()

    main(args.bin)
