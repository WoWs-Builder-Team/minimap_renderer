import json
import os

from renderer_data.gameparams import get_data
from renderer_data.utils import LOGGER


def create_modernization_data():
    LOGGER.info("Creating modernization data...")
    list_modernization = get_data("Modernization")
    modernizations = {}
    modernizations.setdefault("mb_range_modifiers", [])
    modernizations.setdefault("modernizations", {})

    for modernization in list_modernization:
        if hasattr(modernization.modifiers, "GMMaxDist"):
            modernizations["mb_range_modifiers"].append(modernization.id)
        modernizations["modernizations"][
            modernization.id
        ] = {
            "modifiers": modernization.modifiers.__dict__,
            "index": modernization.index
        }

    with open(
        os.path.join(os.getcwd(), "generated", "modernizations.json"), "w"
    ) as f:
        json.dump(modernizations, f)
