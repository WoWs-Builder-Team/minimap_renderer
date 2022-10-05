# coding=utf-8
import struct
from io import BytesIO

from replay_unpack.core import PrettyPrintObjectMixin
from replay_unpack.core.network.types import Vector3


class PlayerPosition(PrettyPrintObjectMixin):
    __slots__ = (
        'entityId1',
        'entityId2',
        'position',
        'yaw',
        'pitch',
        'roll'
    )
    
    def __init__(self, stream):
        # type: (BytesIO) -> ()

        self.entityId1, = struct.unpack('i', stream.read(4))
        self.entityId2, = struct.unpack('i', stream.read(4))

        self.position = Vector3(stream)
        self.yaw, = struct.unpack('f', stream.read(4))
        self.pitch, = struct.unpack('f', stream.read(4))
        self.roll, = struct.unpack('f', stream.read(4))
        