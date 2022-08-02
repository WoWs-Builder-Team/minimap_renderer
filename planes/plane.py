import json
import pickle
import struct
import zlib
import os


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

    with open(
        os.path.join(os.path.dirname(__file__), "plane.json"), "w"
    ) as f:
        json.dump(dict_planes, f, indent=1)

    # for projectile in list_projectile:
    #     if projectile.typeinfo.species == "Torpedo":
    #         dict_projectile[projectile.id] = (
    #             round(projectile.speed / 1.94384),
    #             round(projectile.maxDist * 0.03),
    #         )
    # with open(
    #     os.path.join(os.path.dirname(__file__), "projectile.json"), "w"
    # ) as f:
    #     json.dump(dict_projectile, f, indent=1)

    # mo_file_path = os.path.join(os.path.dirname(__file__), 'global.mo')
    # mo_strings: MOFile = polib.mofile(mo_file_path)
    # dict_strings = {}

    # for mo_string in mo_strings:
    #     mo_string: MOEntry
    #     dict_strings[mo_string.msgid] = mo_string.msgstr

    # dict_ships_info: Dict[int, tuple[str, str, int]] = {}

    # for ship in dict_ships.values():

    #     si = (
    #         dict_strings[f"IDS_{ship.index}"].upper(),
    #         ship.typeinfo.species,
    #         ship.level
    #     )

    #     dict_ships_info[ship.id] = si

    # with open(os.path.join(os.path.dirname(__file__), 'ships.json'), 'w')
    # as f:
    #     json.dump(dict_ships_info, f, indent=1)
