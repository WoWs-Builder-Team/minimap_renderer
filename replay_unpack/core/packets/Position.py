# coding=utf-8
import struct
from io import BytesIO

from replay_unpack.core import PrettyPrintObjectMixin
from replay_unpack.core.network.types import Vector3


class Position(PrettyPrintObjectMixin):
    __slots__ = (
        'entityId',
        'vehicleId',
        'position',
        'positionError',
        'yaw',
        'pitch',
        'roll',
        'is_error'
    )

    def __init__(self, stream):
        self.entityId, = struct.unpack('i', stream.read(4))
        self.vehicleId, = struct.unpack('i', stream.read(4))
        self.position = Vector3(stream)
        self.positionError = Vector3(stream)
        self.yaw, = struct.unpack('f', stream.read(4))
        self.pitch, = struct.unpack('f', stream.read(4))
        self.roll, = struct.unpack('f', stream.read(4))
        self.is_error, = struct.unpack('b', stream.read(1))
