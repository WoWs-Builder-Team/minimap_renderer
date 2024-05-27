from renderer.data import PlayerInfo
from renderer.resman import ResourceManager
import json
import zlib
from base64 import b64encode


class ShipBuilder:
    def __init__(self, resman: ResourceManager) -> None:
        self._abilities = resman.load_json("abilities.json")
        self._ships = resman.load_json("ships.json")
        self._units = resman.load_json("units.json")
        self._modernizations = resman.load_json("modernizations.json")
        self._exteriors = resman.load_json("exteriors.json")

    def get_build(self, player: PlayerInfo) -> tuple[str, str]:
        ship = self._ships[player.ship_params_id]
        modern = self._modernizations["modernizations"]
        abilities = self._abilities[player.ship_params_id][
            "params_id_to_index"
        ]

        name = "renderer"
        ship_index: str = ship["index"]
        ship_nation: str = ship["nation"]
        units = [self._units[v] for v in player.units._asdict().values() if v]
        upgrades = [modern[v]["index"] for v in player.modernization if v]
        captain = "PCW001"
        skills = player.skills.by_species(ship["species"])
        consumables = [abilities[v] for v in player.abilities if v and v in abilities]
        signals = [self._exteriors[v] for v in player.signals if v]
        version = 2

        build_data = {
            "BuildName": name,
            "ShipIndex": ship_index,
            "Nation": ship_nation.replace("_", ""),
            "Modules": units,
            "Upgrades": upgrades,
            "Captain": captain,
            "Skills": skills,
            "Consumables": consumables,
            "Signals": signals,
            "BuildVersion": version,
        }
        b_build_data = json.dumps(build_data).encode()
        deflated = self.deflate(b_build_data)
        build_string = b64encode(deflated).decode()
        build_string = build_string.replace("/", "%2F").replace("+", "%2B")
        return ship_index, build_string

    @staticmethod
    def deflate(data, compresslevel=9):
        compress = zlib.compressobj(
            compresslevel,
            zlib.DEFLATED,
            -zlib.MAX_WBITS,
            zlib.DEF_MEM_LEVEL,
            0,
        )
        deflated = compress.compress(data)
        deflated += compress.flush()
        return deflated
