import json
import os
from renderer_data.gameparams import get_data
from renderer_data.utils import LOGGER


def create_planes_data():
    LOGGER.info("Creating planes data...")
    dict_projectile = {}
    list_projectile = get_data("Projectile")
    list_aircraft = get_data("Aircraft")

    dict_projectile = {p.name: p for p in list_projectile}
    dict_planes = {}

    for aircraft in list_aircraft:
        if bn := aircraft.bombName:
            try:
                at = dict_projectile[bn].ammoType
            except (KeyError, AttributeError):
                at = None
        else:
            at = None

        dict_planes[aircraft.id] = (aircraft.typeinfo.species, at)

    with open(os.path.join(os.getcwd(), "generated", "planes.json"), "w") as f:
        json.dump(dict_planes, f)
