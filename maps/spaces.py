import os
import logging
import shutil
import json

from lxml import etree
from PIL import Image

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s|%(name)s|%(levelname)s|%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOGGER = logging.getLogger("spaces")

BLACKLIST = ["shipyard_", "spaces", "dock", "exterior"]
WHITELIST = ["space.settings", "minimap.png",
             "minimap_water.png", "__init__.py"]


def get_map_size(tree):
    """
    Some map stuff.
    :param tree:
    :return:
    """
    space_bounds, = tree.xpath('/space.settings/bounds')
    if space_bounds.attrib:
        min_x = int(space_bounds.get('minX'))
        min_y = int(space_bounds.get('minY'))
        max_x = int(space_bounds.get('maxX'))
        max_y = int(space_bounds.get('maxY'))
    else:
        min_x = int(space_bounds.xpath('minX/text()')[0])
        min_y = int(space_bounds.xpath('minY/text()')[0])
        max_x = int(space_bounds.xpath('maxX/text()')[0])
        max_y = int(space_bounds.xpath('maxY/text()')[0])

    chunk_size_elements = tree.xpath('/space.settings/chunkSize')
    if chunk_size_elements:
        chunk_size = float(chunk_size_elements[0].text)
    else:
        chunk_size = 100.0

    w = len(range(min_x, max_x + 1)) * chunk_size - 4 * chunk_size
    h = len(range(min_y, max_y + 1)) * chunk_size - 4 * chunk_size
    return w, h


if __name__ == "__main__":
    MAPS = []
    LOGGER.info("Looking for maps, Removing unused files.")

    counter_dirs = 0
    counter_files = 0
    spaces_data = {}

    for fdr in os.walk(os.path.join(os.path.dirname(__file__), "spaces")):
        root, dirs, files = fdr
        base_dir = os.path.basename(os.path.normpath(root))

        if any([True for word in BLACKLIST if word in base_dir.lower()]):
            if base_dir != "spaces":
                try:
                    if os.path.exists(root):
                        shutil.rmtree(root)
                        counter_dirs += 1
                except OSError:
                    LOGGER.info(f"Error at removing dir {root}")
            continue

        to_remove = [os.path.join(root, file)
                     for file in files if file not in WHITELIST]

        for file_to_rm in to_remove:
            try:
                if os.path.exists(file_to_rm):
                    os.remove(file_to_rm)
                    counter_files += 1
            except OSError:
                LOGGER.info(f"Error at removing file: {file_to_rm}")

        minimap_img = Image.open(os.path.join(root, "minimap.png"))

        with open(os.path.join(root, "space.settings"), "r") as reader:
            space_settings = etree.fromstring(
                reader.read(), parser=None)
            space_w, space_h = get_map_size(space_settings)
            space_w, space_h = map(round, (space_w, space_h))

        scaling_w = minimap_img.width / space_w
        scaling_h = minimap_img.height / space_h

        spaces_data[base_dir] = (minimap_img.width, space_w, scaling_w)

        with open(os.path.join(root, "__init__.py"), "w") as f:
            pass

    with open(os.path.join(os.path.dirname(__file__), "spaces",
                           "manifest.json"), "w") as f:
        json.dump(spaces_data, f, indent=1)

    with open(os.path.join(os.path.dirname(__file__), "spaces",
                           "__init__.py"), "w") as f:
        pass

    LOGGER.info("Manifest created.")
    LOGGER.info(
        f"Removed {counter_dirs} directories, {counter_files} file(s).")
    LOGGER.info("Done.")
