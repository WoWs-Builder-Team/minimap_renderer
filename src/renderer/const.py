COLORS_NORMAL = {-1: "#ffffff", 0: "#4ce8aa", 1: "#fe4d2a"}
RELATION_NORMAL_STR = {-1: "self", 0: "ally", 1: "enemy"}
TIER_ROMAN = [
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
]


# for reason in DeathReason.deathReason.getList():
#     print(reason.__dict__)
DEATH_TYPES = {
    0: {"sound": "Health", "icon": "frags", "id": 0, "name": "NONE"},
    1: {"sound": "Health", "icon": "frags", "id": 1, "name": "ARTILLERY"},
    2: {"sound": "ATBA", "icon": "icon_frag_atba", "id": 2, "name": "ATBA"},
    3: {
        "sound": "Torpedo",
        "icon": "icon_frag_torpedo",
        "id": 3,
        "name": "TORPEDO",
    },
    4: {"sound": "Bomb", "icon": "icon_frag_bomb", "id": 4, "name": "BOMB"},
    5: {
        "sound": "Torpedo",
        "icon": "icon_frag_torpedo",
        "id": 5,
        "name": "TBOMB",
    },
    6: {
        "sound": "Burning",
        "icon": "icon_frag_burning",
        "id": 6,
        "name": "BURNING",
    },
    7: {"sound": "RAM", "icon": "icon_frag_ram", "id": 7, "name": "RAM"},
    8: {"sound": "Health", "icon": "frags", "id": 8, "name": "TERRAIN"},
    9: {"sound": "Flood", "icon": "icon_frag_flood", "id": 9, "name": "FLOOD"},
    10: {"sound": "Health", "icon": "frags", "id": 10, "name": "MIRROR"},
    11: {
        "sound": "Torpedo",
        "icon": "icon_frag_naval_mine",
        "id": 11,
        "name": "SEA_MINE",
    },
    12: {"sound": "Health", "icon": "frags", "id": 12, "name": "SPECIAL"},
    13: {
        "sound": "DepthCharge",
        "icon": "icon_frag_depthbomb",
        "id": 13,
        "name": "DBOMB",
    },
    14: {
        "sound": "Rocket",
        "icon": "icon_frag_rocket",
        "id": 14,
        "name": "ROCKET",
    },
    15: {
        "sound": "Detonate",
        "icon": "icon_frag_detonate",
        "id": 15,
        "name": "DETONATE",
    },
    16: {"sound": "Health", "icon": "frags", "id": 16, "name": "HEALTH"},
    17: {
        "sound": "Shell_AP",
        "icon": "icon_frag_main_caliber",
        "id": 17,
        "name": "AP_SHELL",
    },
    18: {
        "sound": "Shell_HE",
        "icon": "icon_frag_main_caliber",
        "id": 18,
        "name": "HE_SHELL",
    },
    19: {
        "sound": "Shell_CS",
        "icon": "icon_frag_main_caliber",
        "id": 19,
        "name": "CS_SHELL",
    },
    20: {"sound": "Fel", "icon": "icon_frag_fel", "id": 20, "name": "FEL"},
    21: {
        "sound": "Portal",
        "icon": "icon_frag_portal",
        "id": 21,
        "name": "PORTAL",
    },
    22: {
        "sound": "SkipBomb",
        "icon": "icon_frag_skip",
        "id": 22,
        "name": "SKIP_BOMB",
    },
    23: {
        "sound": "SECTOR_WAVE",
        "icon": "icon_frag_wave",
        "id": 23,
        "name": "SECTOR_WAVE",
    },
    24: {
        "sound": "Health",
        "icon": "icon_frag_acid",
        "id": 24,
        "name": "ACID",
    },
    25: {
        "sound": "LASER",
        "icon": "icon_frag_laser",
        "id": 25,
        "name": "LASER",
    },
    26: {
        "sound": "Match",
        "icon": "icon_frag_octagon",
        "id": 26,
        "name": "MATCH",
    },
    27: {"sound": "Timer", "icon": "icon_timer", "id": 27, "name": "TIMER"},
    28: {
        "sound": "DepthCharge",
        "icon": "icon_frag_depthbomb",
        "id": 28,
        "name": "ADBOMB",
    },
    # apparently all these event death reasons should have icon FEL
    # but they appear to be 'frags' in game so i have edited them manually
    29: {
        "sound": "Fel",
        "icon": "frags",
        "id": 29,
        "name": "EVENT_1",
    },
    30: {
        "sound": "Fel",
        "icon": "frags",
        "id": 30,
        "name": "EVENT_2",
    },
    31: {
        "sound": "Fel",
        "icon": "frags",
        "id": 31,
        "name": "EVENT_3",
    },
    32: {
        "sound": "Fel",
        "icon": "frags",
        "id": 32,
        "name": "EVENT_4",
    },
    33: {
        "sound": "Fel",
        "icon": "frags",
        "id": 33,
        "name": "EVENT_5",
    },
    34: {
        "sound": "Torpedo",
        "icon": "icon_frag_torpedo",
        "id": 34,
        "name": "EVENT_6",
    },
}

LAYERS = [
    "LayerShip",
    "LayerShot",
    "LayerTorpedo",
    "LayerSmoke",
    "LayerPlane",
    "LayerWard",
    "LayerCapture",
    "LayerHealth",
    "LayerScore",
    "LayerCounter",
    "LayerFrag",
    "LayerTimer",
    "LayerRibbon",
    "LayerChat",
    "LayerBuilding",
    "LayerMarkers",
]
