# coding=utf-8
from replay_unpack.core.packets import (
    EntityControl,
    EntityEnter,
    EntityLeave,
    EntityProperty,
    EntityMethod,
    NestedProperty,
    BasePlayerCreate,
    Position
)
from .CellPlayerCreate import CellPlayerCreate
from .EntityCreate import EntityCreate
from .Map import Map

PACKETS_MAPPING = {
    0x0: BasePlayerCreate,
    0x1: CellPlayerCreate,
    0x2: EntityControl,
    0x3: EntityEnter,
    0x4: EntityLeave,
    0x5: EntityCreate,
    # 0x6
    0x7: EntityProperty,
    0x8: EntityMethod,
    0xf: Map,
    0x24: NestedProperty,
    0x0a: Position
}

__all__ = [
    'EntityMethod',
    'Map',
    'Position',
    'EntityCreate',
    'EntityEnter',
    'EntityLeave',
    'EntityControl',
    'BasePlayerCreate',
    'EntityProperty',
    'CellPlayerCreate',
    'NestedProperty',

    'PACKETS_MAPPING'
]
