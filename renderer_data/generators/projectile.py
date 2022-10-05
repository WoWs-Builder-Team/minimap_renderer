import json
import os
from renderer_data.gameparams import get_data
from renderer_data.utils import LOGGER


def create_projectiles_data():
    LOGGER.info("Creating projectile data...")
    dict_projectile = {}
    list_projectile = get_data("Projectile")

    for projectile in list_projectile:
        if projectile.typeinfo.species == "Artillery":
            dict_projectile[projectile.id] = projectile.ammoType

        if projectile.typeinfo.species == "Torpedo":
            dict_projectile[projectile.id] = (
                round(projectile.speed / 1.94384),
                round(projectile.maxDist * 0.03),
            )

    with open(
        os.path.join(os.getcwd(), "generated", "projectiles.json"), "w"
    ) as f:
        json.dump(dict_projectile, f)
