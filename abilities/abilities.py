import json
import pickle
import struct
import zlib
import os

from GameParams import GPData


class GPEncode(json.JSONEncoder):
    def default(self, o):
        try:
            for e in ["Cameras", "DockCamera", "damageDistribution"]:
                o.__dict__.pop(e, o.__dict__)
            return o.__dict__
        except AttributeError:
            return {}


def get_data(gp_type: str):
    gp_file_path = os.path.join(os.path.dirname(__file__), "GameParams.data")
    with open(gp_file_path, "rb") as f:
        gp_data: bytes = f.read()
        gp_data: bytes = struct.pack("B" * len(gp_data), *gp_data[::-1])
        gp_data: bytes = zlib.decompress(gp_data)
        gp_data_dict: dict = pickle.loads(gp_data, encoding="latin1")
    return filter(
        lambda g: g.typeinfo.type == gp_type, gp_data_dict[0].values()
    )


if __name__ == "__main__":
    dict_abilities = {}
    list_ships = get_data("Ship")
    list_ability = get_data("Ability")

    abilities = {}

    for ab in list_ability:
        for k, v in vars(ab).items():
            if isinstance(v, GPData):
                sub = abilities.setdefault(ab.name, {})
                sub[k] = v.consumableType  # type: ignore

    ability_type_to_id = {
        "crashCrew": 0,
        "airDefenseDisp": 2,
        "sonar": 11,
        "rls": 13,
        "fighter": 10,
        "scout": 1,
        "regenCrew": 9,
        "speedBoosters": 3,
        "torpedoReloader": 12,
        "hydrophone": 35,
        "smokeGenerator": 7,
        "artilleryBoosters": 5,
        "trigger1": 14,
        "trigger2": 15,
        "trigger3": 16,
        "trigger4": 17,
        "trigger5": 18,
        "trigger6": 19,
        "trigger7": 28,
        "trigger8": 29,
        "trigger9": 30,
        "fastRudders": 36,
        "subsEnergyFreeze": 37,
        "invisibilityExtraBuffConsumable": 40,
        "goDeep": 33,
        "circleWave": 32,
        "affectedBuffAura": 39,
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
                    at[ability_type_to_id[sa]] = name


    with open(
        os.path.join(os.path.dirname(__file__), "abilities.json"), "w"
    ) as f:
        json.dump(ship_abilities, f, indent=1)
