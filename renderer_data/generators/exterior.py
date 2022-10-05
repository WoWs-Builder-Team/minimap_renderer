import json
import os

from renderer_data.gameparams import get_data
from renderer_data.gameparams.GameParams import GPData
from renderer_data.utils import LOGGER


def create_exterior_data():
    LOGGER.info("Creating building data...")
    list_exterior = get_data("Exterior")

    dict_exterior = {}

    for exterior in list_exterior:
        dict_exterior[exterior.id] = exterior.name

    with open(
        os.path.join(os.getcwd(), "generated", "exteriors.json"), "w"
    ) as f:
        json.dump(dict_exterior, f)
