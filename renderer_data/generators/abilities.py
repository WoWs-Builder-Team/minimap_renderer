import functools
import json
import os

from renderer_data.gameparams import get_data
from renderer_data.utils import LOGGER

REQUIRED = {
    "workTime",
    "logic.regenerationHPSpeed",
    "logic.distShip",
    "logic.artilleryDistCoeff",
}
# ConsumablesConstants.ConsumableIDsMap
ability_type_to_id = {'tacticalTrigger2': 46, 'callFighters': 21, 'smokePlane': 52, 'goDeep': 33,
                      'weaponReloadBooster': 34, 'planeMinefield': 43, 'subsEnergyFreeze': 37, 'All': 55,
                      'planeSmokeGenerator': 42, 'submarineLocator': 41, 'trigger4': 16, 'trigger5': 17,
                      'trigger6': 18, 'trigger7': 27, 'smokeGenerator': 6, 'trigger1': 13, 'trigger2': 14,
                      'trigger3': 15, 'tacticalTrigger3': 47, 'invulnerable': 19, 'tacticalTrigger1': 45,
                      'trigger8': 28, 'trigger9': 29, 'tacticalTrigger5': 49, 'tacticalTrigger4': 48,
                      'reconnaissanceSquad': 51, 'airDefenseDisp': 2, 'torpedoReloader': 11, 'minefield': 44,
                      'fastRudders': 36, 'buff': 30, 'healForsage': 20, 'hydrophone': 35, 'subsFourthState': 25,
                      'regenCrew': 8, 'tacticalBuff': 53, 'scout': 1, 'artilleryBoosters': 4, 'groupAuraBuff': 38,
                      'buffsShift': 31, 'invisibilityExtraBuffConsumable': 40, 'regenerateHealth': 22, 'rls': 12,
                      'subsOxygenRegen': 23, 'circleWave': 32, 'affectedBuffAura': 39, 'fighter': 9, 'crashCrew': 0,
                      'Any': 54, 'hangarBoosters': 5, 'Special': 56, 'speedBoosters': 3, 'sonar': 10,
                      'subsWaveGunBoost': 24, 'tacticalTrigger6': 50, 'depthCharges': 26}


# https://gist.github.com/wonderbeyond/d293e7a2af1de4873f2d757edd580288
def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))


def create_abilities_data():
    LOGGER.info("Creating abilities data...")
    list_ships = get_data("Ship")
    list_ability = get_data("Ability")

    clan_battles = {}
    ability_entities = {}

    for ab in list_ability:
        for k, v in vars(ab).items():
            if "ClanBattles" in k:
                type_id = ability_type_to_id[v.consumableType]
                assert type_id not in clan_battles, "Duplicate clan battle consumable types"
                clan_battles[type_id] = ab.name

            sub = ability_entities.setdefault(ab.name, {})
            sub[k] = v  # type: ignore

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
                    at[f"{name}.{sub_name}"] = {}
                    for key in REQUIRED:
                        try:
                            at.setdefault(f"{name}.{sub_name}", {})[key[key.rfind(".") + 1:]] = rgetattr(sa, key)
                        except AttributeError:
                            pass

    _abils["clan"] = clan_battles

    with open(
            os.path.join(os.getcwd(), "generated", "abilities.json"), "w"
    ) as f:
        json.dump(_abils, f)
