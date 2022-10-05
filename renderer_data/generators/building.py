import json
import os

from renderer_data.gameparams import get_data
from renderer_data.gameparams.GameParams import GPData
from renderer_data.utils import LOGGER


def create_building_data():
    LOGGER.info("Creating building data...")
    list_building = get_data("Building")

    dict_buildings = {}

    for building in list_building:
        dict_buildings[building.id] = building.typeinfo.species

    with open(
        os.path.join(os.getcwd(), "generated", "buildings.json"), "w"
    ) as f:
        json.dump(dict_buildings, f)
