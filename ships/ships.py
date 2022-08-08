import json
import pickle
import struct
import zlib
import polib
import os

from polib import MOFile, MOEntry
from typing import Dict


class GPEncode(json.JSONEncoder):
    def default(self, o):
        try:
            for e in ['Cameras', 'DockCamera', 'damageDistribution']:
                o.__dict__.pop(e, o.__dict__)
            return o.__dict__
        except AttributeError:
            return {}


def get_gp_dict():
    gp_file_path = os.path.join(os.path.dirname(__file__), 'GameParams.data')
    with open(gp_file_path, "rb") as f:
        gp_data: bytes = f.read()
        gp_data: bytes = struct.pack('B' * len(gp_data), *gp_data[::-1])
        gp_data: bytes = zlib.decompress(gp_data)
        gp_data_dict: dict = pickle.loads(gp_data, encoding='latin1')
    return gp_data_dict


if __name__ == '__main__':
    dict_ships = {}
    gp_dict = get_gp_dict()
    list_ships = filter(lambda g: g.typeinfo.type == 'Ship',
                        gp_dict[0].values())
    list_units = filter(lambda g: g.typeinfo.type == 'Unit',
                        gp_dict[0].values())
    units_name_to_id = {unit.name: unit.id for unit in list_units}

    for ship in list_ships:
        dict_ships[ship.id] = ship

    mo_file_path = os.path.join(os.path.dirname(__file__), 'global.mo')
    mo_strings: MOFile = polib.mofile(mo_file_path)
    dict_strings = {}

    for mo_string in mo_strings:
        mo_string: MOEntry
        dict_strings[mo_string.msgid] = mo_string.msgstr

    dict_ships_info: Dict[int, tuple[str, str, str, int, dict[str, int]]] = {}

    for ship in dict_ships.values():
        hulls = {}
        for key, value in ship.ShipUpgradeInfo.__dict__.items():
            try:
                if value.ucType == '_Hull':
                    hull_name = value.components['hull'][0]
                    hull = getattr(ship, hull_name)
                    hulls[units_name_to_id[key]] = [len(hull.burnNodes), len(hull.floodNodes)]

            except AttributeError:
                continue

        si = (
            ship.index,
            dict_strings[f"IDS_{ship.index}"].upper(),
            ship.typeinfo.species,
            ship.level,
            hulls,
        )

        dict_ships_info[ship.id] = si
    #
    # for unit in list_units:
    #     for ship in dict_ships_info.values():
    #         if ship[4].get(unit.name, None):
    #             ship[4][unit.id] = ship[4].pop(unit.name)

    with open(os.path.join(os.path.dirname(__file__), 'ships.json'), 'w') as f:
        json.dump(dict_ships_info, f, indent=1)
