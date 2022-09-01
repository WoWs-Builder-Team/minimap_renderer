from typing import NamedTuple, Optional


class Units(NamedTuple):
    hull: int
    artillery: int
    torpedoes: int
    suo: int
    engine: int
    flight_control: int
    fighter: int
    torpedo_bomber: int
    dive_bomber: int
    hydrophone: int
    skip_bomber: int
    primary_weapons: int
    secondary_weapons: int
    abilities: int


class PlayerInfo(NamedTuple):
    """Player information"""

    account_db_id: int
    id: int
    clan_color: int
    clan_id: int
    clan_tag: str
    max_health: int
    name: str
    realm: str
    ship_id: int
    team_id: int
    is_bot: bool
    ship_params_id: int
    relation: int
    hull: Optional[int]
    abilities: tuple
    modernization: tuple
    skills: list[list[int]]
    ship_components: dict
    units: Optional[Units] = None
    signals: Optional[tuple] = None


class Vehicle(NamedTuple):
    """Vehicle data."""

    player_id: int
    vehicle_id: int
    health: int
    is_alive: bool
    x: int
    y: int
    yaw: float
    relation: int
    is_visible: bool
    not_in_range: bool
    visibility_flag: int
    burn_flags: int
    consumables_state: dict[int, tuple]
    regenerated_health: float = 0.0
    regen_crew_hp_limit: float = 0.0
    regeneration_health: float = 0.0

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return (self.is_alive < other.is_alive) or (
                self.is_visible < other.is_visible
            )
        raise TypeError


class BuildingInfo(NamedTuple):
    """Building information"""

    id: int
    is_alive: bool
    is_hidden: bool
    is_suppressed: bool
    name: str
    params_id: int
    team_id: int
    unique_id: int
    relation: int
    ship_params_id: int
    clan_tag: str = ""


class Building(NamedTuple):
    is_alive: bool
    is_suppressed: bool
    is_visible: bool
    x: int
    y: int
    yaw: int


class Smoke(NamedTuple):
    """Smoke data."""

    entity_id: int
    radius: float
    points: list[tuple[int, int]]


class Shot(NamedTuple):
    """Shot data."""

    owner_id: int
    params_id: int
    origin: tuple[int, int]
    destination: tuple[int, int]
    shot_id: int
    t_time: int


class Torpedo(NamedTuple):
    """Torpedo data."""

    owner_id: int
    params_id: int
    origin: tuple[int, int]
    direction: tuple[float, float]
    shot_id: int


class Consumable(NamedTuple):
    """Consumable data."""

    ship_id: int
    consumable_id: int
    duration: float


class Plane(NamedTuple):
    """Plane data."""

    plane_id: int
    owner_id: int
    params_id: int
    index: int
    purpose: int
    departures: int
    relation: int
    position: tuple[int, int]


class Ward(NamedTuple):
    """Ward data."""

    plane_id: int
    vehicle_id: int
    position: tuple[int, int]
    radius: int
    relation: int


class ControlPoint(NamedTuple):
    position: tuple[int, int]
    radius: int
    team_id: int
    invader_team: int
    control_point_type: int
    progress: float
    both_inside: bool
    has_invaders: bool
    capture_time: int
    capture_speed: float
    relation: int
    is_visible: bool


class Score(NamedTuple):
    relation: int
    score: int


class Frag(NamedTuple):
    killed_id: int
    fragger_id: int
    death_type: int


class Message(NamedTuple):
    player_id: int
    namespace: str
    message: str


class BattleResult(NamedTuple):
    team_id: int
    victory_type: int


class Events(NamedTuple):
    """Match events."""

    time_left: int
    evt_vehicle: dict[int, Vehicle]
    evt_building: dict[int, Building]
    evt_plane: dict[int, Plane]
    evt_ward: dict[int, Ward]
    evt_smoke: dict[int, Smoke]
    evt_shot: list[Shot]
    evt_torpedo: list[Torpedo]
    evt_hits: list[int]
    evt_consumable: dict[int, list[Consumable]]
    evt_control: dict[int, ControlPoint]
    evt_score: dict[int, Score]
    evt_damage_maps: dict[str, dict[int, tuple[int, float]]]
    evt_frag: list[Frag]
    evt_ribbon: dict
    evt_achievement: dict
    evt_times_to_win: Optional[tuple[float, float]]
    evt_chat: list[Message]
    last_frame: bool = False


class ReplayData(NamedTuple):
    """Replay data."""

    game_arena_id: int
    game_version: str
    game_map: str
    game_battle_type: int
    game_win_score: int
    game_result: BattleResult
    owner_avatar_id: int
    owner_vehicle_id: int
    owner_id: int
    player_info: dict[int, PlayerInfo]
    building_info: dict[int, BuildingInfo]
    events: dict[int, Events]
