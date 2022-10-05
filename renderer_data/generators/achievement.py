import json
import os

from renderer_data.gameparams import get_data
from renderer_data.utils import LOGGER


def create_achievements_data():
    LOGGER.info("Creating achievement data...")
    list_achievement = get_data("Achievement")

    dict_achievement = {}

    for achievement in list_achievement:
        dict_achievement[achievement.id] = achievement.uiName

    with open(
        os.path.join(os.getcwd(), "generated", "achievements.json"), "w"
    ) as f:
        json.dump(dict_achievement, f)
