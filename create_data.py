from data.utils import LOGGER

from data import (
    create_ships_data,
    create_planes_data,
    create_projectile_data,
    create_achievement_data,
    create_abilities_data,
)


if __name__ == "__main__":
    create_ships_data()
    create_planes_data()
    create_projectile_data()
    create_achievement_data()
    create_abilities_data()
    LOGGER.info("Done.")
