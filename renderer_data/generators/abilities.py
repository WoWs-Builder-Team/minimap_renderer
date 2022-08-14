import json
import os

from renderer_data.gameparams import get_data
from renderer_data.gameparams.GameParams import GPData
from renderer_data.utils import LOGGER


def create_abilities_data():
    LOGGER.info("Creating abilities data...")
    list_ships = get_data("Ship")
    list_ability = get_data("Ability")

    abilities = {}

    for ab in list_ability:
        for k, v in vars(ab).items():
            if isinstance(v, GPData):
                sub = abilities.setdefault(ab.name, {})
                sub[k] = v  # type: ignore

    ability_type_to_id = {
        "crashCrew": 0,
        "scout": 1,
        "airDefenseDisp": 2,
        "speedBoosters": 3,
        "artilleryBoosters": 5,
        "smokeGenerator": 7,
        "regenCrew": 9,
        "fighter": 10,
        "sonar": 11,
        "torpedoReloader": 12,
        "rls": 13,
        "trigger1": 14,
        "trigger2": 15,
        "trigger3": 16,
        "trigger4": 17,
        "trigger5": 18,
        "trigger6": 19,
        "trigger7": 28,
        "trigger8": 29,
        "trigger9": 30,
        "circleWave": 32,
        "goDeep": 33,
        "hydrophone": 35,
        "fastRudders": 36,
        "subsEnergyFreeze": 37,
        "affectedBuffAura": 39,
        "invisibilityExtraBuffConsumable": 40,
        "submarineLocator": 41,
    }
    ship_abilities = {}

    for ship in list_ships:
        for abilityslot in [
            getattr(ship.ShipAbilities, i)
            for i in dir(ship.ShipAbilities)
            if "AbilitySlot" in i
        ]:
            if ability := abilityslot.abils:
                at = ship_abilities.setdefault(ship.id, {})

                for abs in abilityslot.abils:
                    name, sub_name = abs
                    sa = abilities[name][sub_name]

                    if sa.consumableType == "regenCrew":
                        at["regenerationHPSpeed"] = sa.regenerationHPSpeed
                        at["workTime"] = sa.workTime

                    at[ability_type_to_id[sa.consumableType]] = name

    with open(
        os.path.join(os.getcwd(), "generated", "abilities.json"), "w"
    ) as f:
        json.dump(ship_abilities, f)
