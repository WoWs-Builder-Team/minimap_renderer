# coding=utf-8
import copy
import logging
import math
import struct

from io import BytesIO
from replay_unpack.core import IBattleController
from replay_unpack.core.entity import Entity
from replay_unpack.core.entity_def.data_types.nested_types import PyFixedDict
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
    Message,
    BattleResult,
    BuildingInfo,
    Building,
    Units,
    Skills,
    AcousticTorpedo,
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
        self._arena_id: int = 0
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
        Entity.subscribe_method_call(
            "Vehicle", "setConsumables", self.onSetConsumable
        )
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
        self._dict_building_info: dict[int, BuildingInfo] = {}
        self._dict_vehicle: dict[int, Vehicle] = {}
        self._dict_building: dict[int, Building] = {}
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
        self._battle_result_nt: BattleResult = BattleResult(-1, -1)

        # ACCUMULATORS #

        self._acc_shots: list[Shot] = []
        self._acc_torpedoes: dict[int, Torpedo] = {}
        self._acc_hits: list[int] = []
        self._acc_consumables: dict[int, list[Consumable]] = {}
        self._acc_frags: list[Frag] = []
        self._acc_message: list[Message] = []
        self._acc_acoustic_torpedoes: dict[int, AcousticTorpedo] = {}

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
        Entity.subscribe_property_change(
            "BattleLogic", "battleResult", self._set_battle_result
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
            "SmokeScreen", "points", self._set_smoke_points
        )
        Entity.subscribe_property_change(
            "BattleLogic", "state", self._set_state
        )
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
        Entity.subscribe_method_call(
            "Avatar", "onChatMessage", self._on_chat_message
        )
        Entity.subscribe_property_change(
            "Vehicle", "burningFlags", self._set_burning_flags
        )
        Entity.subscribe_property_change(
            "Building", "isSuppressed", self._is_suppressed
        )
        Entity.subscribe_property_change("Building", "isAlive", self._is_alive)
        Entity.subscribe_method_call(
            "Avatar", "receiveTorpedoDirection", self._receive_torpedo_dir
        )
        Entity.subscribe_property_change(
            "Vehicle", "maxHealth", self._set_max_health
        )
        Entity.subscribe_property_change(
            "InteractiveZone", "componentsState", self._set_caps
        )
        Entity.subscribe_nested_property_change(
            "InteractiveZone", "componentsState.captureLogic", self._update_caps
        )
        Entity.subscribe_nested_property_change(
            "Avatar", "privateVehicleState.ribbons", self._update_ribbons
        )

    ###########################################################################

    def _update_caps(self, entity: Entity, cp_l):
        cp = entity.properties["client"]

        if not cp["componentsState"]["controlPoint"]:
            return

        if cp["teamId"] == self._owner["teamId"] and cp["teamId"] != -1:
            relation = 0
        elif cp["teamId"] != self._owner["teamId"] and cp["teamId"] != -1:
            relation = 1
        else:
            relation = -1

        cid = cp["componentsState"]["controlPoint"]["index"]
        self._dict_control[cid] = ControlPoint(
            position=(round(entity.position.x), round(entity.position.z)),
            radius=cp["radius"],
            team_id=cp["teamId"],
            invader_team=cp_l["invaderTeam"],
            control_point_type=cp["componentsState"]["controlPoint"]["type"],
            progress=cp_l["progress"],
            both_inside=cp_l["bothInside"],
            has_invaders=cp_l["hasInvaders"],
            capture_time=cp_l["captureTime"],
            capture_speed=cp_l["captureSpeed"],
            relation=relation,
            is_visible=cp_l["isVisible"],
        )

    def _set_caps(self, entity: Entity, state):
        if not state["controlPoint"]:
            return

        cp = entity.properties["client"]
        cp_l = state["captureLogic"]

        if cp["teamId"] == self._owner["teamId"] and cp["teamId"] != -1:
            relation = 0
        elif cp["teamId"] != self._owner["teamId"] and cp["teamId"] != -1:
            relation = 1
        else:
            relation = -1

        cid = state["controlPoint"]["index"]

        self._dict_control[cid] = ControlPoint(
            position=(round(entity.position.x), round(entity.position.z)),
            radius=cp["radius"],
            team_id=cp["teamId"],
            invader_team=cp_l["invaderTeam"],
            control_point_type=state["controlPoint"]["type"],
            progress=cp_l["progress"],
            both_inside=cp_l["bothInside"],
            has_invaders=cp_l["hasInvaders"],
            capture_time=cp_l["captureTime"],
            capture_speed=cp_l["captureSpeed"],
            relation=relation,
            is_visible=cp_l["isVisible"],
        )

    def _set_max_health(self, entity: Entity, max_health):
        pid = self._vehicle_to_id[entity.id]
        self._dict_info[pid] = self._dict_info[pid]._replace(
            max_health=max_health
        )

    # receiveTorpedoDirection(self, ownerId, torpedoId, serverPos, targetYaw,
    # targetDepth, speedCoef, curYawSpeed, curPitchSpeed, canReachDepth)

    def _receive_torpedo_dir(
        self,
        entity: Entity,
        vehicle_id: int,
        shot_id: int,
        pos: tuple,
        t_yaw,
        t_depth,
        speed_coef,
        cur_yaw_speed,
        cur_pitch_speed,
        can_reach_depth,
    ):
        x, y = map(round, pos[::2])
        self._acc_acoustic_torpedoes[
            int(f"{vehicle_id}{shot_id}")
        ] = AcousticTorpedo(
            vehicle_id,
            int(f"{vehicle_id}{shot_id}"),
            x,
            y,
            t_yaw,
            cur_yaw_speed,
        )

    def _is_suppressed(self, entity: Entity, val):
        self._dict_building[entity.id] = self._dict_building[
            entity.id
        ]._replace(is_suppressed=val)

    def _is_alive(self, entity: Entity, val):
        self._dict_building[entity.id] = self._dict_building[
            entity.id
        ]._replace(is_alive=val)

    def _on_chat_message(
        self, entity: Entity, player_id, namespace, message, unk
    ):
        if player_id in [0, -1]:
            return

        self._acc_message.append(
            Message(player_id=player_id, namespace=namespace, message=message)
        )

    def set_packet_time(self, t: float):
        self._packet_time = t

    def _set_burning_flags(self, entity, flags):
        self._dict_vehicle[entity.id] = self._dict_vehicle[entity.id]._replace(
            burn_flags=flags
        )

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

    def _add_ward(
        self, entity, plane_id, position, radius, duration, team_id, vehicle_id
    ):
        radius = radius if radius else 60
        self._dict_ward[plane_id] = Ward(
            plane_id=plane_id,
            position=tuple(map(round, position[::2])),
            radius=radius,
            relation=self._dict_info[self._vehicle_to_id[vehicle_id]].relation,
            vehicle_id=vehicle_id,
        )

    def _remove_ward(self, entity, plane_id):
        self._dict_ward.pop(plane_id)

    @staticmethod
    def _time_to_win(reward, period, score_left):
        if not reward:
            return -1

        return period * score_left / reward

    def _times_to_win(self):
        if not self._time_left:
            return None

        try:
            # TODO: drop assumption that all caps have same property?
            mission = self.battle_logic.properties["client"]["state"][
                "missions"
            ]["hold"][0]
            reward, period = mission["reward"], mission["period"]
        except (TypeError, IndexError, KeyError):
            return None

        ally_tick, enemy_tick = 0, 0
        for cap in self._dict_control.values():
            if not cap.both_inside and cap.team_id != -1:
                if cap.relation == 0:
                    ally_tick += reward
                else:
                    enemy_tick += reward

        ally_ttw = self._time_to_win(
            ally_tick, period, self._win_score - self._dict_score[0].score
        )
        enemy_ttw = self._time_to_win(
            enemy_tick, period, self._win_score - self._dict_score[1].score
        )
        return ally_ttw, enemy_ttw

    def _update(self, entity, time_left):
        self._time_left = time_left

        if self._battle_stage != 0:
            return

        battle_time = self._durations[-1] - self._time_left
        evt = Events(
            time_left=self._time_left,
            evt_vehicle=copy.copy(self._dict_vehicle),
            evt_building=copy.copy(self._dict_building),
            evt_smoke=copy.copy(self._dict_smoke),
            evt_shot=copy.copy(self._acc_shots),
            evt_torpedo=copy.copy(self._acc_torpedoes),
            evt_hits=copy.copy(self._acc_hits),
            evt_consumable=copy.copy(self._acc_consumables),
            evt_plane=copy.copy(self._dict_plane),
            evt_ward=copy.copy(self._dict_ward),
            evt_control=dict(sorted(self._dict_control.items())),
            evt_score=copy.copy(self._dict_score),
            evt_damage_maps=copy.deepcopy(self._damage_maps),
            evt_frag=copy.copy(self._acc_frags),
            evt_ribbon=copy.deepcopy(self._ribbons),
            evt_times_to_win=self._times_to_win(),
            evt_achievement=copy.deepcopy(self._achievements),
            evt_chat=copy.deepcopy(self._acc_message),
            evt_acoustic_torpedo=copy.deepcopy(self._acc_acoustic_torpedoes),
        )

        self._dict_events[battle_time] = evt
        self._acc_shots.clear()
        self._acc_torpedoes.clear()
        self._acc_hits.clear()
        self._acc_consumables.clear()
        self._acc_frags.clear()
        self._acc_message.clear()
        self._acc_acoustic_torpedoes.clear()

    def _add_plane(
        self, entity: Entity, plane_id: int, team_id, params_id, pos, unk
    ):
        owner_id, index, purpose, departures = unpack_plane_id(plane_id)

        try:
            relation = self._dict_info[self._vehicle_to_id[owner_id]].relation
        except KeyError:
            if self._owner["teamId"] == team_id and team_id != -1:
                relation = 0
            elif self._owner["teamId"] != team_id and team_id != -1:
                relation = 1
            else:
                relation = -1

        self._dict_plane[plane_id] = Plane(
            plane_id=plane_id,
            owner_id=owner_id,
            params_id=params_id,
            index=index,
            purpose=purpose,
            departures=departures,
            relation=relation,
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
                yaw = math.atan2(a, b)
                speed_bw = math.hypot(a, b)
                shot_id = torpedo["shotID"]
                self._acc_torpedoes[int(f"{owner_id}{shot_id}")] = Torpedo(
                    params_id=shot["paramsID"],
                    owner_id=owner_id,
                    origin=(x, y),
                    shot_id=int(f"{owner_id}{torpedo['shotID']}"),
                    yaw=yaw,
                    speed_bw=speed_bw,
                )

    def _crew_skills(self, entity: Entity, params):
        self._dict_info[self._vehicle_to_id[entity.id]] = self._dict_info[
            self._vehicle_to_id[entity.id]
        ]._replace(skills=Skills(*params["learnedSkills"]))

    def _modernization(self, entity: Entity, config: bytes):

        with BytesIO(config) as bio:
            # bio.seek(3 * 4, 1)
            (unknown_1,) = struct.unpack("<L", bio.read(4))
            (ship_params_id,) = struct.unpack("<L", bio.read(4))
            (unknown_2,) = struct.unpack("<L", bio.read(4))
            (d,) = struct.unpack("<L", bio.read(4))  # len
            units = struct.unpack("<" + "L" * d, bio.read(4 * d))
            u = Units(*units)
            hull_unit = units[0]
            (e,) = struct.unpack("<L", bio.read(4))  # modernization slot len
            modern = struct.unpack("<" + "L" * e, bio.read(e * 4))
            (f,) = struct.unpack("<L", bio.read(4))
            signals = struct.unpack("<" + "L" * f, bio.read(4 * f))
            (supply_state,) = struct.unpack("<L", bio.read(4))
            (h,) = struct.unpack("<L", bio.read(4))
            for i in range(h):
                camo = struct.unpack("<" + "L", bio.read(4))
                camo_scheme = struct.unpack("<L", bio.read(4))

            (i,) = struct.unpack("<L", bio.read(4))
            abilities = struct.unpack("<" + "L" * i, bio.read(4 * i))

            try:
                self._dict_info[
                    self._vehicle_to_id[entity.id]
                ] = self._dict_info[self._vehicle_to_id[entity.id]]._replace(
                    abilities=abilities,
                    hull=hull_unit,
                    modernization=modern,
                    units=u,
                    signals=signals,
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
                        shot["paramsID"],
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
        if entity.id == 959830:
            exit()

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
        for e in buildings_minimap_diff:
            vehicle_id = e["vehicleID"]
            x, y, yaw = unpack_values(e["packedData"], pack_pattern)
            x, y, yaw = map(round, (x, y, math.degrees(yaw)))
            is_visible = x != -2500 or y != -2500

            if is_visible:
                self._dict_building[vehicle_id] = self._dict_building[
                    vehicle_id
                ]._replace(x=x, y=y, yaw=yaw, is_visible=is_visible)
            else:
                self._dict_building[vehicle_id] = self._dict_building[
                    vehicle_id
                ]._replace(is_visible=is_visible)

        for e in ships_minimap_diff:
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

    def _set_smoke_points(self, entity: Entity, points):
        self._dict_smoke[entity.id] = self._dict_smoke[entity.id]._replace(
            points=copy.copy(points)
        )

    def _create_player_vehicle_data(self):
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

            if player["playerType"] == 3:
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

            if player["playerType"] in [1, 2]:
                pi = PlayerInfo(
                    id=player["id"],
                    account_db_id=player["accountDBID"],
                    clan_color=player["clanColor"],
                    clan_id=player["clanID"],
                    clan_tag=player["clanTag"],
                    max_health=player["maxHealth"],
                    name=player["name"].encode('ISO8859-1').decode('UTF-8'),
                    realm=player["realm"],
                    ship_id=player["shipId"],
                    team_id=player["teamId"],
                    is_bot=bool(player["isBot"]),
                    ship_params_id=player["shipParamsId"],
                    relation=relation,
                    hull=None,
                    abilities=(),
                    modernization=(),
                    skills=Skills(),
                    ship_components=player["shipComponents"],
                )

                self._dict_info.setdefault(player["id"], pi)
                self._vehicle_to_id.setdefault(player["shipId"], player["id"])

                vi = Vehicle(
                    player_id=player["id"],
                    vehicle_id=player["shipId"],
                    health=player["maxHealth"],
                    is_alive=True,
                    x=-2500,
                    y=-2500,
                    yaw=-180,
                    relation=relation,
                    is_visible=False,
                    not_in_range=False,
                    visibility_flag=0,
                    burn_flags=0,
                    consumables_state={},
                )
                self._dict_vehicle.setdefault(player["shipId"], vi)

            elif player["playerType"] == 4:
                bi = BuildingInfo(
                    id=player["id"],
                    is_alive=player["isAlive"],
                    is_hidden=player["isHidden"],
                    is_suppressed=player["isSuppressed"],
                    name=player["name"].encode('ISO8859-1').decode('UTF-8'),
                    params_id=player["paramsId"],
                    team_id=player["teamId"],
                    unique_id=player["uniqueId"],
                    relation=relation,
                    ship_params_id=player["paramsId"],
                )

                self._dict_building_info.setdefault(player["id"], bi)

                building = Building(
                    is_alive=player["isAlive"],
                    is_suppressed=player["isSuppressed"],
                    is_visible=False,
                    x=-2500,
                    y=-2500,
                    yaw=-180,
                )

                self._dict_building.setdefault(player["id"], building)

    ###########################################################################

    def onSetConsumable(self, vehicle, blob):
        consumables = {}
        for c in restricted_loads(blob, encoding="latin1"):
            cid, state = c
            consumables[cid] = state

        self._dict_vehicle[vehicle.id] = self._dict_vehicle[
            vehicle.id
        ]._replace(consumables_state=consumables)

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
        # force copy of last frame to handle subsecond events
        battle_time = self._durations[-1] - self._time_left + 1
        evt = Events(
            time_left=self._time_left,
            evt_vehicle=copy.copy(self._dict_vehicle),
            evt_building=copy.copy(self._dict_building),
            evt_smoke=copy.copy(self._dict_smoke),
            evt_shot=copy.copy(self._acc_shots),
            evt_torpedo=copy.copy(self._acc_torpedoes),
            evt_hits=copy.copy(self._acc_hits),
            evt_consumable=copy.copy(self._acc_consumables),
            evt_plane=copy.copy(self._dict_plane),
            evt_ward=copy.copy(self._dict_ward),
            evt_control=dict(sorted(self._dict_control.items())),
            evt_score=copy.copy(self._dict_score),
            evt_damage_maps=copy.deepcopy(self._damage_maps),
            evt_frag=copy.copy(self._acc_frags),
            evt_ribbon=copy.deepcopy(self._ribbons),
            evt_times_to_win=self._times_to_win(),
            evt_achievement=copy.deepcopy(self._achievements),
            evt_chat=copy.deepcopy(self._acc_message),
            evt_acoustic_torpedo=copy.deepcopy(self._acc_acoustic_torpedoes),
            last_frame=True,
        )

        self._dict_events[battle_time] = evt

        # adding killed planes data
        players = copy.deepcopy(self._players.get_info())
        for player in players.values():
            player["planesCount"] = self._dead_planes.get(
                player.get("shipId", 0), 0
            )

        rd = ReplayData(
            game_arena_id=self._arena_id,
            game_version=self._version[:-2].replace(",", "_"),
            game_map=self._map,
            game_battle_type=self._battle_type,
            game_win_score=self._win_score,
            game_result=self._battle_result_nt,
            owner_avatar_id=self._owner["avatarId"],
            owner_vehicle_id=self._owner["shipId"],
            owner_id=self._owner["id"],
            player_info=self._dict_info,
            building_info=self._dict_building_info,
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

    def onBattleEnd(self, avatar):
        # TODO: mark true game end time as of 12.5.0
        pass

    def _set_battle_result(self, entity, battle_result):
        self._battle_result_nt = self._battle_result_nt._replace(
            team_id=battle_result["winnerTeamId"], victory_type=battle_result["finishReason"]
        )
        self._battle_result = dict(
            winner_team_id=battle_result["winnerTeamId"], victory_type=battle_result["finishReason"]
        )

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
            restricted_loads(buildingsInfo, encoding="latin1"),
            PlayerType.BUILDING,
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

    def receiveDamageStat(self, avatar, blob):
        normalized_map = {}

        for (type_, bool_), value in restricted_loads(blob).items():
            if (name := DamageStatsType.names[bool_]) not in normalized_map:
                normalized_map[name] = {}

            normalized_map[name].setdefault(type_, {})
            normalized_map[name][type_] = tuple(value)

        for name, normalized in normalized_map.items():
            self._damage_maps[name].update(normalized)

    def _update_ribbons(self, avatar, ribbons_state):
        def update_ribbons(state):
            self._ribbons.setdefault(avatar.id, {})[state["ribbonId"]] = state["count"]

        if isinstance(ribbons_state, PyFixedDict):
            update_ribbons(ribbons_state)
        else:
            for s in ribbons_state:
                update_ribbons(s)

    # def onRibbon(self, vehicle, ribbon_id):
    #     self._ribbons.setdefault(vehicle.id, {}).setdefault(ribbon_id, 0)
    #     self._ribbons[vehicle.id][ribbon_id] += 1

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
    def map(self, value: str):
        self._map = value.removeprefix("spaces/")
