# coding=utf-8

id_property_map = {0: 'accountDBID', 1: 'antiAbuseEnabled', 2: 'avatarId', 3: 'camouflageInfo',
                   4: 'clanColor', 5: 'clanID', 6: 'clanTag', 7: 'crewParams', 8: 'dogTag',
                   9: 'fragsCount', 10: 'friendlyFireEnabled', 11: 'id', 12: 'invitationsEnabled',
                   13: 'isAbuser', 14: 'isAlive', 15: 'isBot', 16: 'isClientLoaded', 17: 'isConnected',
                   18: 'isHidden', 19: 'isLeaver', 20: 'isPreBattleOwner', 21: 'isTShooter',
                   22: 'killedBuildingsCount', 23: 'maxHealth', 24: 'name', 25: 'playerMode',
                   26: 'preBattleIdOnStart', 27: 'preBattleSign', 28: 'prebattleId', 29: 'realm',
                   30: 'shipComponents', 31: 'shipConfigDump', 32: 'shipId', 33: 'shipParamsId',
                   34: 'skinId', 35: 'teamId', 36: 'ttkStatus'}
property_id_map = {value: key for key, value in id_property_map.items()}

# ModsShell.API_v_1_0.battleGate.PlayersInfo.gSharedBotInfo._numMemberMap
id_property_map_bots = {0: 'accountDBID', 1: 'antiAbuseEnabled', 2: 'camouflageInfo', 3: 'clanColor',
                        4: 'clanID', 5: 'clanTag', 6: 'crewParams', 7: 'dogTag', 8: 'fragsCount',
                        9: 'friendlyFireEnabled', 10: 'id', 11: 'isAbuser', 12: 'isAlive',
                        13: 'isBot', 14: 'isHidden', 15: 'isTShooter', 16: 'killedBuildingsCount',
                        17: 'maxHealth', 18: 'name', 19: 'realm', 20: 'shipComponents', 21: 'shipConfigDump',
                        22: 'shipId', 23: 'shipParamsId', 24: 'skinId', 25: 'teamId', 26: 'ttkStatus'}
property_id_map_bots = {value: key for key, value in id_property_map.items()}


# ModsShell.API_v_1_0.battleGate.PlayersInfo.gSharedObserverInfo._numMemberMap
id_property_map_observer = {0: 'accountDBID', 1: 'avatarId', 2: 'dogTag', 3: 'id', 4: 'invitationsEnabled', 5: 'isAlive',
                            6: 'isClientLoaded', 7: 'isConnected', 8: 'isLeaver', 9: 'isPreBattleOwner', 10: 'name',
                            11: 'playerMode', 12: 'preBattleIdOnStart', 13: 'preBattleSign', 14: 'prebattleId',
                            15: 'realm', 16: 'teamId'}
property_id_map_bots_observer = {value: key for key, value in id_property_map.items()}



class DamageStatsType:
    """See Avatar.DamageStatsType"""
    DAMAGE_STATS_ENEMY = 0
    DAMAGE_STATS_ALLY = 1
    DAMAGE_STATS_SPOT = 2
    DAMAGE_STATS_AGRO = 3


class Category(object):
    """Category of task to separate for UI"""

    CHALLENGE = 4
    PRIMARY = 1
    SECONDARY = 2
    TERTIARY = 3

    ids = {'Challenge': 4, 'Primary': 1, 'Secondary': 2, 'Tertiary': 3}
    names = {1: 'Primary', 2: 'Secondary', 3: 'Tertiary', 4: 'Challenge'}


class Status(object):
    CANCELED = 4
    FAILURE = 3
    IN_PROGRESS = 1
    NOT_STARTED = 0
    SUCCESS = 2
    UPDATED = 5

    ids = {'Updated': 5, 'Success': 2, 'Canceled': 4, 'NotStarted': 0, 'Failure': 3, 'InProgress': 1}
    names = {0: 'NotStarted', 1: 'InProgress', 2: 'Success', 3: 'Failure', 4: 'Canceled', 5: 'Updated'}


class TaskType(object):
    DIGIT = 1
    DIGIT_SINGLE = 5
    NO_TYPE = 0
    PROGRESS_BAR = 4
    REVERSED_TIMER = 3
    TIMER = 2

    names = {0: 'NoType', 1: 'Digit', 2: 'Timer', 3: 'ReversedTimer', 4: 'ProgressBar', 5: 'DigitSingle'}
    ids = {'ReversedTimer': 3, 'Digit': 1, 'DigitSingle': 5, 'Timer': 2, 'ProgressBar': 4, 'NoType': 0}


# {i: vars(j) for i,j in Vehicle.DeathReason._DeathReason__byId.items()}
DEATH_TYPES = {
    0: {'sound': 'Health', 'icon': 'frags', 'id': 0, 'name': 'NONE'},
    1: {'sound': 'Health', 'icon': 'frags', 'id': 1, 'name': 'ARTILLERY'},
    2: {'sound': 'ATBA', 'icon': 'icon_frag_atba', 'id': 2, 'name': 'ATBA'},
    3: {'sound': 'Torpedo', 'icon': 'icon_frag_torpedo', 'id': 3, 'name': 'TORPEDO'},
    4: {'sound': 'Bomb', 'icon': 'icon_frag_bomb', 'id': 4, 'name': 'BOMB'},
    5: {'sound': 'Torpedo', 'icon': 'icon_frag_torpedo', 'id': 5, 'name': 'TBOMB'},
    6: {'sound': 'Burning', 'icon': 'icon_frag_burning', 'id': 6, 'name': 'BURNING'},
    7: {'sound': 'RAM', 'icon': 'icon_frag_ram', 'id': 7, 'name': 'RAM'},
    8: {'sound': 'Health', 'icon': 'frags', 'id': 8, 'name': 'TERRAIN'},
    9: {'sound': 'Flood', 'icon': 'icon_frag_flood', 'id': 9, 'name': 'FLOOD'},
    10: {'sound': 'Health', 'icon': 'frags', 'id': 10, 'name': 'MIRROR'},
    11: {'sound': 'Torpedo', 'icon': 'icon_frag_naval_mine', 'id': 11, 'name': 'SEA_MINE'},
    12: {'sound': 'Health', 'icon': 'frags', 'id': 12, 'name': 'SPECIAL'},
    13: {'sound': 'DepthCharge', 'icon': 'icon_frag_depthbomb', 'id': 13, 'name': 'DBOMB'},
    14: {'sound': 'Rocket', 'icon': 'icon_frag_rocket', 'id': 14, 'name': 'ROCKET'},
    15: {'sound': 'Detonate', 'icon': 'icon_frag_detonate', 'id': 15, 'name': 'DETONATE'},
    16: {'sound': 'Health', 'icon': 'frags', 'id': 16, 'name': 'HEALTH'},
    17: {'sound': 'Shell_AP', 'icon': 'icon_frag_main_caliber', 'id': 17, 'name': 'AP_SHELL'},
    18: {'sound': 'Shell_HE', 'icon': 'icon_frag_main_caliber', 'id': 18, 'name': 'HE_SHELL'},
    19: {'sound': 'Shell_CS', 'icon': 'icon_frag_main_caliber', 'id': 19, 'name': 'CS_SHELL'},
    20: {'sound': 'Fel', 'icon': 'icon_frag_fel', 'id': 20, 'name': 'FEL'},
    21: {'sound': 'Portal', 'icon': 'icon_frag_portal', 'id': 21, 'name': 'PORTAL'},
    22: {'sound': 'SkipBomb', 'icon': 'icon_frag_skip', 'id': 22, 'name': 'SKIP_BOMB'},
    23: {'sound': 'SECTOR_WAVE', 'icon': 'icon_frag_wave', 'id': 23, 'name': 'SECTOR_WAVE'},
    24: {'sound': 'Health', 'icon': 'icon_frag_acid', 'id': 24, 'name': 'ACID'},
    25: {'sound': 'LASER', 'icon': 'icon_frag_laser', 'id': 25, 'name': 'LASER'},
    26: {'sound': 'Match', 'icon': 'icon_frag_octagon', 'id': 26, 'name': 'MATCH'},
    27: {'sound': 'Timer', 'icon': 'icon_timer', 'id': 27, 'name': 'TIMER'},
    28: {'sound': 'DepthCharge', 'icon': 'icon_frag_depthbomb', 'id': 28, 'name': 'ADBOMB'}
}
