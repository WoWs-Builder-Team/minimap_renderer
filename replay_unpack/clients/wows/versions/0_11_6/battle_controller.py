# coding=utf-8
import copy
import logging
import math
import struct

from io import BytesIO
from replay_unpack.core import IBattleController
from replay_unpack.core.entity import Entity
from .constants import DamageStatsType, Category, TaskType, Status

from renderer.data import (
    PlayerInfo,
    Vehicle,
    ReplayData,
    Events,
    Smoke,
    Shot,
    Torpedo,
    Consumable,
    Plane,
    Ward,
    ControlPoint,
    Score,
    Frag,
)
from replay_unpack.utils import (
    unpack_values,
    unpack_plane_id,
    restricted_loads,
)


try:
    from .constants import DEATH_TYPES
except ImportError:
    DEATH_TYPES = {}
from .players_info import PlayersInfo, PlayerType


class BattleController(IBattleController):
    def __init__(self):
        self._entities = {}
        self._achievements = {}
        self._ribbons = {}
        self._players = PlayersInfo()
        self._battle_result = None
        self._damage_maps = {name: {} for name in DamageStatsType.ids}
        self._shots_damage_map = {}
        self._death_map = []
        self._map = ""
        self._player_id = None
        self._arena_id = None
        self._dead_planes = {}

        Entity.subscribe_method_call("Avatar", "onBattleEnd", self.onBattleEnd)
        Entity.subscribe_method_call(
            "Avatar", "onArenaStateReceived", self.onArenaStateReceived
        )
        Entity.subscribe_method_call(
            "Avatar", "onGameRoomStateChanged", self.onPlayerInfoUpdate
        )
        Entity.subscribe_method_call(
            "Avatar", "receiveVehicleDeath", self.receiveVehicleDeath
        )
        # Entity.subscribe_method_call(
        #     "Vehicle", "setConsumables", self.onSetConsumable
        # )
        Entity.subscribe_method_call("Avatar", "onRibbon", self.onRibbon)
        Entity.subscribe_method_call(
            "Avatar", "onAchievementEarned", self.onAchievementEarned
        )
        Entity.subscribe_method_call(
            "Avatar", "receiveDamageStat", self.receiveDamageStat
        )
        Entity.subscribe_method_call(
            "Avatar", "receive_planeDeath", self.receive_planeDeath
        )
        Entity.subscribe_method_call(
            "Avatar",
            "onNewPlayerSpawnedInBattle",
            self.onNewPlayerSpawnedInBattle,
        )
        Entity.subscribe_method_call(
            "Vehicle", "receiveDamagesOnShip", self.g_receiveDamagesOnShip
        )

        #######################################################################
        self._owner: dict = {}
        self._durations: list[int] = []
        self._time_left: int = 0
        self._battle_stage: int = -1
        self._dict_info: dict[int, PlayerInfo] = {}
        self._dict_vehicle: dict[int, Vehicle] = {}
        self._dict_smoke: dict[int, Smoke] = {}
        self._dict_plane: dict[int, Plane] = {}
        self._dict_ward: dict[int, Ward] = {}
        self._dict_score: dict[int, Score] = {}
        self._dict_control: dict[int, ControlPoint] = {}
        self._vehicle_to_id: dict[int, int] = {}
        self._dict_events: dict[int, Events] = {}
        self._version: str = ""
        self._battle_type: int = 0
        self._win_score: int = 1000
        self._packet_time: float = 0.0

        # ACCUMULATORS #

        self._acc_shots: list[Shot] = []
        self._acc_torpedoes: list[Torpedo] = []
        self._acc_hits: list[int] = []
        self._acc_consumables: dict[int, list[Consumable]] = {}
        self._acc_frags: list[Frag] = []

        #######################################################################

        Entity.subscribe_property_change(
            "BattleLogic", "timeLeft", self._update
        )
        Entity.subscribe_property_change(
            "BattleLogic", "duration", self._set_durations
        )
        Entity.subscribe_property_change(
            "BattleLogic", "battleStage", self._set_battle_stage
        )
        Entity.subscribe_property_change("Vehicle", "health", self._set_health)
        Entity.subscribe_property_change(
            "Vehicle", "isAlive", self._set_is_alive
        )
        Entity.subscribe_method_call(
            "Avatar", "updateMinimapVisionInfo", self._update_position
        )
        Entity.subscribe_property_change(
            "Vehicle", "isInvisible", self._set_is_invisible
        )
        Entity.subscribe_method_call(
            "Avatar",
            "receiveArtilleryShots",
            self._r_shots,
        )
        Entity.subscribe_method_call(
            "Avatar", "receiveTorpedoes", self._receiveTorpedoes
        )

        Entity.subscribe_property_change(
            "Vehicle", "shipConfig", self._modernization
        )

        Entity.subscribe_property_change(
            "Vehicle", "crewModifiersCompactParams", self._crew_skills
        )

        Entity.subscribe_method_call(
            "Avatar", "receiveShotKills", self._set_hits
        )

        Entity.subscribe_property_change(
            "Vehicle", "visibilityFlags", self._set_visibility_flag
        )

        Entity.subscribe_method_call(
            "Vehicle",
            "consumableUsed",
            self._on_consumable_used,
        )
        Entity.subscribe_method_call(
            "Avatar",
            "receive_addMinimapSquadron",
            self._add_plane,
        )
        Entity.subscribe_method_call(
            "Avatar",
            "receive_addMinimapSquadron",
            self._add_plane,
        )
        Entity.subscribe_method_call(
            "Avatar", "receive_updateMinimapSquadron", self._update_plane
        )
        Entity.subscribe_method_call(
            "Avatar", "receive_removeMinimapSquadron", self._remove_plane
        )

        Entity.subscribe_method_call(
            "Avatar", "receive_wardAdded", self._add_ward
        )

        Entity.subscribe_method_call(
            "Avatar", "receive_wardRemoved", self._remove_ward
        )
        Entity.subscribe_nested_property_change(
            "BattleLogic", "state.controlPoints", self._set_control_points
        )
        Entity.subscribe_nested_property_change(
            "SmokeScreen", "points", self._set_smoke_points
        )
        Entity.subscribe_property_change(
            "BattleLogic", "state", self._set_state
        )
        # Entity.subscribe_nested_property_change(
        #     "BattleLogic",
        #     "state.missions.teamsScore",
        #     lambda *a, **b: print(a, b),
        # )
        Entity.subscribe_property_change(
            "BattleLogic", "battleType", self._set_battle_type
        )

        Entity.subscribe_nested_property_change(
            "BattleLogic",
            "state.missions.teamsScore",
            self._set_score,
        )
        Entity.subscribe_property_change(
            "Vehicle", "regeneratedHealth", self._set_regenerated_health
        )
        Entity.subscribe_property_change(
            "Vehicle", "regenCrewHpLimit", self._set_regen_crew_hp_limit
        )
        Entity.subscribe_property_change(
            "Vehicle", "regenerationHealth", self._set_regeneration_health
        )

    ###########################################################################

    def set_packet_time(self, t: float):
        self._packet_time = t

    def _set_regenerated_health(self, entity, health):
        self._dict_vehicle[entity.id] = self._dict_vehicle[entity.id]._replace(
            regenerated_health=health
        )

    def _set_regen_crew_hp_limit(self, entity, health):
        self._dict_vehicle[entity.id] = self._dict_vehicle[entity.id]._replace(
            regen_crew_hp_limit=health
        )

    def _set_regeneration_health(self, entity, health):
        self._dict_vehicle[entity.id] = self._dict_vehicle[entity.id]._replace(
            regeneration_health=health
        )

    def _set_score(self, entity, score):
        if score["teamId"] == self._owner["teamId"]:
            relation = 0
        else:
            relation = 1
        self._dict_score[relation] = self._dict_score[relation]._replace(
            score=score["score"]
        )

    def _set_battle_type(self, entity, battle_type):
        self._battle_type = battle_type

    def _set_state(self, entity, state):
        self._win_score = state["missions"]["teamWinScore"]

        for team_score in state["missions"]["teamsScore"]:
            if team_score["teamId"] == self._owner["teamId"]:
                relation = 0
            else:
                relation = 1
            self._dict_score[relation] = Score(relation, team_score["score"])

        for cp in state["controlPoints"]:
            if cp["teamId"] == self._owner["teamId"] and cp["teamId"] != -1:
                relation = 0
            elif cp["teamId"] != self._owner["teamId"] and cp["teamId"] != -1:
                relation = 1
            else:
                relation = -1

            cid = hash(tuple(cp["position"])) & 1000000000
            self._dict_control[cid] = ControlPoint(
                position=tuple(map(round, cp["position"])),
                radius=cp["radius"],
                team_id=cp["teamId"],
                invader_team=cp["invaderTeam"],
                control_point_type=cp["controlPointType"],
                progress=cp["progress"],
                both_inside=bool(cp["bothInside"]),
                has_invaders=bool(cp["hasInvaders"]),
                capture_time=cp["captureTime"],
                capture_speed=cp["captureSpeed"],
                relation=relation,
                is_visible=cp["isVisible"],
            )

    def _set_control_points(self, ent, cp):
        if cp["teamId"] == self._owner["teamId"] and cp["teamId"] != -1:
            relation = 0
        elif cp["teamId"] != self._owner["teamId"] and cp["teamId"] != -1:
            relation = 1
        else:
            relation = -1

        cid = hash(tuple(cp["position"])) & 1000000000
        self._dict_control[cid] = self._dict_control[cid]._replace(
            position=tuple(map(round, cp["position"])),
            radius=cp["radius"],
            team_id=cp["teamId"],
            invader_team=cp["invaderTeam"],
            control_point_type=cp["controlPointType"],
            progress=cp["progress"],
            both_inside=bool(cp["bothInside"]),
            has_invaders=bool(cp["hasInvaders"]),
            capture_time=cp["captureTime"],
            capture_speed=cp["captureSpeed"],
            relation=relation,
            is_visible=bool(cp["isVisible"]),
        )

    def _add_ward(
        self, entity, plane_id, position, radius, duration, team_id, vehicle_id
    ):
        self._dict_ward[plane_id] = Ward(
            plane_id=plane_id,
            position=tuple(map(round, position[::2])),
            radius=radius,
            relation=self._dict_info[self._vehicle_to_id[vehicle_id]].relation,
            vehicle_id=vehicle_id,
        )

    def _remove_ward(self, entity, plane_id):
        self._dict_ward.pop(plane_id)

    def _update(self, entity, time_left):
        self._time_left = time_left

        if self._battle_stage != 0:
            return

        battle_time = self._durations[-1] - self._time_left
        evt = Events(
            time_left=self._time_left,
            evt_vehicle=copy.copy(self._dict_vehicle),
            evt_smoke=copy.copy(self._dict_smoke),
            evt_shot=copy.copy(self._acc_shots),
            evt_torpedo=copy.copy(self._acc_torpedoes),
            evt_hits=copy.copy(self._acc_hits),
            evt_consumable=copy.copy(self._acc_consumables),
            evt_plane=copy.copy(self._dict_plane),
            evt_ward=copy.copy(self._dict_ward),
            evt_control=copy.copy(self._dict_control),
            evt_score=copy.copy(self._dict_score),
            evt_damage_maps=copy.deepcopy(self._damage_maps),
            evt_frag=copy.copy(self._acc_frags),
        )

        self._dict_events[battle_time] = evt
        self._acc_shots.clear()
        self._acc_torpedoes.clear()
        self._acc_hits.clear()
        self._acc_consumables.clear()
        self._acc_frags.clear()

    def _add_plane(
        self, entity: Entity, plane_id: int, team_id, params_id, pos, unk
    ):
        owner_id, index, purpose, departures = unpack_plane_id(plane_id)
        # print(owner_id, index, purpose, departures, pos, params_id)
        self._dict_plane[plane_id] = Plane(
            plane_id=plane_id,
            owner_id=owner_id,
            params_id=params_id,
            index=index,
            purpose=purpose,
            departures=departures,
            relation=self._dict_info[self._vehicle_to_id[owner_id]].relation,
            position=tuple(map(round, pos)),
        )

    def _update_plane(self, entity: Entity, plane_id: int, pos):

        self._dict_plane[plane_id] = self._dict_plane[plane_id]._replace(
            position=tuple(map(round, pos))
        )

    def _remove_plane(self, entity: Entity, plane_id: int):
        self._dict_plane.pop(plane_id)

    def _on_consumable_used(self, entity: Entity, cid, dur):
        consumables = self._acc_consumables.setdefault(entity.id, [])
        consumables.append(
            Consumable(ship_id=entity.id, consumable_id=cid, duration=dur)
        )

    def _set_visibility_flag(self, entity: Entity, flag: int):
        self._dict_vehicle[entity.id] = self._dict_vehicle[entity.id]._replace(
            visibility_flag=flag
        )

    def _set_hits(self, entity: Entity, data):
        for item in data:
            for kill in item["kills"]:
                self._acc_hits.append(
                    int(f"{item['ownerID']}{kill['shotID']}")
                )

    def _receiveTorpedoes(self, entity: Entity, shots):
        for shot in shots:
            owner_id = shot["ownerID"]
            for torpedo in shot["torpedoes"]:
                x, y = map(round, torpedo["pos"][::2])
                a, b = torpedo["dir"][::2]

                self._acc_torpedoes.append(
                    Torpedo(
                        params_id=shot["paramsID"],
                        owner_id=owner_id,
                        origin=(x, y),
                        direction=(a, b),
                        shot_id=int(f"{owner_id}{torpedo['shotID']}"),
                    )
                )

    def _crew_skills(self, entity: Entity, params):
        self._dict_info[self._vehicle_to_id[entity.id]] = self._dict_info[
            self._vehicle_to_id[entity.id]
        ]._replace(skills=params["learnedSkills"])

    def _modernization(self, entity: Entity, config: bytes):
        with BytesIO(config) as bio:
            bio.seek(3 * 4, 1)
            (d,) = struct.unpack("<L", bio.read(4))  # len
            bio.seek(4 * d, 1)
            (e,) = struct.unpack("<L", bio.read(4))  # modernization slot len
            modern = struct.unpack("<" + "L" * e, bio.read(e * 4))

            (f,) = struct.unpack("<L", bio.read(4))
            signals = struct.unpack("<" + "L" * f, bio.read(4 * f))
            (supply_state,) = struct.unpack("<L", bio.read(4))

            (h,) = struct.unpack("<L", bio.read(4))
            if h:
                camo = struct.unpack("<" + "L" * h, bio.read(4 * h))
                camo_scheme = struct.unpack("<L", bio.read(4))

            (i,) = struct.unpack("<L", bio.read(4))
            abilities = struct.unpack("<" + "L" * i, bio.read(4 * i))

            # print(abilities)

            # inter = any(set(modern).intersection([4220702640, 4219654064]))
            # print(entity.id, modern, inter)
            try:
                self._dict_info[
                    self._vehicle_to_id[entity.id]
                ] = self._dict_info[self._vehicle_to_id[entity.id]]._replace(
                    modernization=modern
                )
            except KeyError:
                pass

    def _r_shots(self, entity: Entity, shots: list):
        for shot in shots:
            owner_id = shot["ownerID"]
            for projectile in shot["shots"]:
                t_time = round(projectile["serverTimeLeft"] / 2.75)
                x1, y1 = map(round, projectile["pos"][::2])
                x2, y2 = map(round, projectile["tarPos"][::2])
                self._acc_shots.append(
                    Shot(
                        owner_id,
                        (x1, y1),
                        (x2, y2),
                        int(f"{owner_id}{projectile['shotID']}"),
                        t_time,
                    )
                )

    def _set_durations(self, entity, duration):
        self._durations.append(duration)

    def _set_battle_stage(self, entity, battle_stage):
        self._battle_stage = battle_stage

    def _set_health(self, entity: Entity, health):
        self._dict_vehicle[entity.id] = self._dict_vehicle[entity.id]._replace(
            health=health
        )

    def _set_is_alive(self, entity: Entity, is_alive):
        self._dict_vehicle[entity.id] = self._dict_vehicle[entity.id]._replace(
            is_alive=bool(is_alive)
        )

    def _set_is_invisible(self, entity: Entity, is_invisible):
        self._dict_vehicle[entity.id] = self._dict_vehicle[entity.id]._replace(
            not_in_range=bool(is_invisible)
        )

    def _update_position(
        self, entity: Entity, ships_minimap_diff, buildings_minimap_diff
    ):
        pack_pattern = (
            (-2500.0, 2500.0, 11),
            (-2500.0, 2500.0, 11),
            (-3.141592753589793, 3.141592753589793, 8),
        )
        for e in ships_minimap_diff:
            try:
                vehicle_id = e["vehicleID"]
                x, y, yaw = unpack_values(e["packedData"], pack_pattern)
                x, y, yaw = map(round, (x, y, math.degrees(yaw)))

                is_visible = x != -2500 or y != -2500

                if is_visible:
                    self._dict_vehicle[vehicle_id] = self._dict_vehicle[
                        vehicle_id
                    ]._replace(x=x, y=y, yaw=yaw, is_visible=is_visible)
                else:
                    self._dict_vehicle[vehicle_id] = self._dict_vehicle[
                        vehicle_id
                    ]._replace(is_visible=is_visible)
            except KeyError:
                pass

    def _set_smoke_points(self, entity: Entity, points):
        self._dict_smoke[entity.id] = self._dict_smoke[entity.id]._replace(
            points=copy.copy(points)
        )

    def _create_player_vehicle_data(self, update=False):
        if not self._owner:
            for player in self._players.get_info().values():
                try:
                    if player["avatarId"] == self._player_id:
                        self._owner = player
                except KeyError:
                    pass

        for player in self._players.get_info().values():
            if not self._owner:
                continue
            is_ally = self._owner["teamId"] == player["teamId"]

            try:
                is_owner = self._owner["avatarId"] == player["avatarId"]
            except KeyError:
                is_owner = self._owner["avatarId"] == player["id"]

            if is_ally and not is_owner:
                relation = 0
            elif not is_ally and not is_owner:
                relation = 1
            else:
                relation = -1

            pi = PlayerInfo(
                avatar_id=player["id"],
                account_db_id=player["accountDBID"],
                clan_color=player["clanColor"],
                clan_id=player["clanID"],
                clan_tag=player["clanTag"],
                max_health=player["maxHealth"],
                name=player["name"],
                realm=player["realm"],
                ship_id=player["shipId"],
                team_id=player["teamId"],
                is_bot=bool(player["isBot"]),
                ship_params_id=player["shipParamsId"],
                relation=relation,
                modernization=(),
                skills=[],
            )
            self._vehicle_to_id[player["shipId"]] = player["id"]
            self._dict_info[player["id"]] = pi

            if update:
                continue

            vi = Vehicle(
                avatar_id=player["id"],
                vehicle_id=player["shipId"],
                health=player["maxHealth"],
                is_alive=True,
                x=-2500,
                y=-2500,
                yaw=-180,
                relation=relation,
                is_visible=False,
                not_in_range=True,
                visibility_flag=0,
            )
            self._dict_vehicle[player["shipId"]] = vi

    ###########################################################################

    def onSetConsumable(self, vehicle, blob):
        print(restricted_loads(blob, encoding="latin1"))

    @property
    def entities(self):
        return self._entities

    @property
    def battle_logic(self):
        return next(
            e for e in self._entities.values() if e.get_name() == "BattleLogic"
        )

    def create_entity(self, entity: Entity):
        self._entities[entity.id] = entity

        if entity.get_name() == "SmokeScreen":
            radius = entity.properties["client"]["radius"]
            points: list = list(entity.properties["client"]["points"])

            if entity.id not in self._dict_smoke:
                self._dict_smoke[entity.id] = Smoke(
                    entity_id=entity.id, radius=radius, points=points
                )
            else:
                self._dict_smoke[entity.id]._replace(
                    radius=radius, points=points
                )

    def destroy_entity(self, entity: Entity):
        self._entities.pop(entity.id)

    def leave_entity(self, entity_id):
        if entity_id in self._dict_smoke:
            self._dict_smoke.pop(entity_id)

    def on_player_enter_world(self, entity_id: int):
        self._player_id = entity_id

    def get_info(self):
        # adding killed planes data
        players = copy.deepcopy(self._players.get_info())
        for player in players.values():
            player["planesCount"] = self._dead_planes.get(
                player.get("shipId", 0), 0
            )

        rd = ReplayData(
            game_version=self._version[:-2].replace(",", "_"),
            game_map=self._map,
            game_battle_type=self._battle_type,
            game_win_score=self._win_score,
            player_info=self._dict_info,
            events=self._dict_events,
        )

        return dict(
            achievements=self._achievements,
            ribbons=self._ribbons,
            players=players,
            battle_result=self._battle_result,
            damage_maps=self._damage_maps,
            shots_damage_map=self._shots_damage_map,
            death_map=self._death_map,
            death_info=self._getDeathsInfo(),
            map=self._map,
            player_id=self._player_id,
            control_points=self._getCapturePointsInfo(),
            tasks=list(self._getTasksInfo()),
            skills=dict(),
            arena_id=self._arena_id,
            replay_data=rd,
        )

    def _getDeathsInfo(self):
        deaths = {}
        for killedVehicleId, fraggerVehicleId, typeDeath in self._death_map:
            death_type = DEATH_TYPES.get(typeDeath)
            if death_type is None:
                logging.warning("Unknown death type %s", typeDeath)
                continue

            deaths[killedVehicleId] = {
                "killer_id": fraggerVehicleId,
                "icon": death_type["icon"],
                "name": death_type["name"],
            }
        return deaths

    def _getCapturePointsInfo(self):
        return self.battle_logic.properties["client"]["state"].get(
            "controlPoints", []
        )

    def _getTasksInfo(self):
        tasks = self.battle_logic.properties["client"]["state"].get(
            "tasks", []
        )
        for task in tasks:
            yield {
                "category": Category.names[task["category"]],
                "status": Status.names[task["status"]],
                "name": task["name"],
                "type": TaskType.names[task["type"]],
            }

    def onBattleEnd(self, avatar, teamId, state):
        self._battle_result = dict(winner_team_id=teamId, victory_type=state)

    def onNewPlayerSpawnedInBattle(
        self, entity, playersData, botsData, observersData
    ):
        self._players.create_or_update_players(
            restricted_loads(playersData, encoding="latin1"), PlayerType.PLAYER
        )
        self._players.create_or_update_players(
            restricted_loads(botsData, encoding="latin1"), PlayerType.BOT
        )
        self._players.create_or_update_players(
            restricted_loads(observersData, encoding="latin1"),
            PlayerType.OBSERVER,
        )
        self._create_player_vehicle_data()

    def onArenaStateReceived(
        self,
        avatar,
        arenaUniqueId,
        teamBuildTypeId,
        preBattlesInfo,
        playersStates,
        botsStates,
        observersState,
        buildingsInfo,
    ):
        self._arena_id = arenaUniqueId
        self._players.create_or_update_players(
            restricted_loads(playersStates, encoding="latin1"),
            PlayerType.PLAYER,
        )
        self._players.create_or_update_players(
            restricted_loads(botsStates, encoding="latin1"), PlayerType.BOT
        )
        self._players.create_or_update_players(
            restricted_loads(observersState, encoding="latin1"),
            PlayerType.OBSERVER,
        )
        self._create_player_vehicle_data()

    def onPlayerInfoUpdate(self, avatar, playersData, botsData, observersData):
        self._players.create_or_update_players(
            restricted_loads(playersData, encoding="latin1"), PlayerType.PLAYER
        )
        self._players.create_or_update_players(
            restricted_loads(botsData, encoding="latin1"), PlayerType.BOT
        )
        self._players.create_or_update_players(
            restricted_loads(observersData, encoding="latin1"),
            PlayerType.OBSERVER,
        )
        self._create_player_vehicle_data(True)

    def receiveDamageStat(self, avatar, blob):
        normalized_map = {}

        for (type_, bool_), value in restricted_loads(blob).items():
            if (name := DamageStatsType.names[bool_]) not in normalized_map:
                normalized_map[name] = {}

            normalized_map[name].setdefault(type_, {})
            normalized_map[name][type_] = tuple(value)

        for name, normalized in normalized_map.items():
            self._damage_maps[name].update(normalized)

    def onRibbon(self, avatar, ribbon_id):
        self._ribbons.setdefault(avatar.id, {}).setdefault(ribbon_id, 0)
        self._ribbons[avatar.id][ribbon_id] += 1

    def onAchievementEarned(self, avatar, avatar_id, achievement_id):
        self._achievements.setdefault(avatar_id, {}).setdefault(
            achievement_id, 0
        )
        self._achievements[avatar_id][achievement_id] += 1

    def receiveVehicleDeath(
        self, avatar, killedVehicleId, fraggerVehicleId, typeDeath
    ):
        self._acc_frags.append(
            Frag(
                killed_id=killedVehicleId,
                fragger_id=fraggerVehicleId,
                death_type=typeDeath,
            )
        )
        self._death_map.append((killedVehicleId, fraggerVehicleId, typeDeath))

    def g_receiveDamagesOnShip(self, vehicle, damages):
        for damage_info in damages:
            self._shots_damage_map.setdefault(vehicle.id, {}).setdefault(
                damage_info["vehicleID"], 0
            )
            self._shots_damage_map[vehicle.id][
                damage_info["vehicleID"]
            ] += damage_info["damage"]

    def receive_planeDeath(
        self, avatar, squadronID, planeIDs, reason, attackerId
    ):
        self._dead_planes.setdefault(attackerId, 0)
        self._dead_planes[attackerId] += len(planeIDs)

    @property
    def map(self):
        raise NotImplementedError()

    @map.setter
    def map(self, value):
        self._map = value.lstrip("spaces/")
