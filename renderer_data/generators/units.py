import json
import os

from renderer_data.gameparams import get_data
from renderer_data.gameparams.GameParams import GPData
from renderer_data.utils import LOGGER


def create_units_data():
    LOGGER.info("Creating units data...")
    list_units = get_data("Unit")

    dict_units = {}

    for unit in list_units:
        dict_units[unit.id] = unit.name

    with open(
        os.path.join(os.getcwd(), "generated", "units.json"), "w"
    ) as f:
        json.dump(dict_units, f)
