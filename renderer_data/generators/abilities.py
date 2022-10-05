import json
import os

from renderer_data.gameparams import get_data
from renderer_data.utils import LOGGER


REQUIRED = {
    "workTime",
    "regenerationHPSpeed",
    "distShip",
    "artilleryDistCoeff",
}


def create_abilities_data():
    LOGGER.info("Creating abilities data...")
    list_ships = get_data("Ship")
    list_ability = get_data("Ability")

    ability_entities = {}

    for ab in list_ability:
        for k, v in vars(ab).items():
            sub = ability_entities.setdefault(ab.name, {})
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
    _abils = {}

    for ship in list_ships:
        for abilityslot in [
            getattr(ship.ShipAbilities, i)
            for i in dir(ship.ShipAbilities)
            if "AbilitySlot" in i
        ]:
            if ship_abilities := abilityslot.abils:
                at = _abils.setdefault(ship.id, {})
                id_to_type = at.setdefault("id_to_subtype", {})
                id_to_index = at.setdefault("id_to_index", {})
                params_id_to_subtype = at.setdefault(
                    "params_id_to_subtype", {}
                )
                params_id_to_index = at.setdefault("params_id_to_index", {})

                for abs in ship_abilities:
                    name, sub_name = abs
                    ability = ability_entities[name]
                    sa = ability[sub_name]
                    id_to_type[
                        ability_type_to_id[sa.consumableType]
                    ] = sub_name
                    id_to_index[ability_type_to_id[sa.consumableType]] = name
                    params_id_to_subtype[ability["id"]] = sub_name
                    params_id_to_index[ability["id"]] = ability["index"]
                    at[f"{name}.{sub_name}"] = {
                        k: v for k, v in sa.__dict__.items() if k in REQUIRED
                    }

    with open(
        os.path.join(os.getcwd(), "generated", "abilities.json"), "w"
    ) as f:
        json.dump(_abils, f)
