# coding=utf-8
import struct

from replay_unpack.core import PrettyPrintObjectMixin
from replay_unpack.core.network.types import BinaryStream
from replay_unpack.core.network.types import Vector3


class CellPlayerCreate(PrettyPrintObjectMixin):
    def __init__(self, stream):
        self.entityId, = struct.unpack('i', stream.read(4))
        self.spaceId, = struct.unpack('i', stream.read(4))
        self.vehicleId, = struct.unpack('i', stream.read(4))
        self.position = Vector3(stream)
        self.direction = Vector3(stream)

        self.value = BinaryStream(stream)
