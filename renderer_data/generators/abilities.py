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
        'callFighters': 21,
        'goDeep': 32,
        'weaponReloadBooster': 33, 'planeMinefield': 42,
        'subsEnergyFreeze': 36,
        'All': 44,
        'planeSmokeGenerator': 41,
        'submarineLocator': 40,
        'trigger4': 16,
        'trigger5': 17,
        'trigger6': 18,
        'trigger7': 27,
        'smokeGenerator': 6,
        'trigger1': 13,
        'trigger2': 14,
        'trigger3': 15,
        'beffsShift': 30,
        'invulnerable': 19,
        'trigger8': 28,
        'trigger9': 29,
        'airDefenseDisp': 2,
        'torpedoReloader': 11,
        'fastRudders': 35,
        'healForsage': 20,
        'hydrophone': 34,
        'subsFourthState': 25,
        'regenCrew': 8,
        'scout': 1,
        'artilleryBoosters': 4,
        'groupAuraBuff': 37,
        'invisibilityExtraBuffConsumable': 39,
        'regenerateHealth': 22,
        'rls': 12,
        'subsOxygenRegen': 23,
        'circleWave': 31,
        'affectedBuffAura': 38,
        'fighter': 9,
        'crashCrew': 0,
        'hangarBoosters': 5,
        'speedBoosters': 3,
        'sonar': 10,
        'subsWaveGunBoost': 24,
        'Any': 43,
        'depthCharges': 26
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
