# coding=utf-8
import struct

from replay_unpack.core import PrettyPrintObjectMixin


class Vector3(PrettyPrintObjectMixin):
    __slots__ = (
        'x', 'y', 'z',
    )

    def __init__(self, stream):
        self.x, = struct.unpack('f', stream.read(4))
        self.y, = struct.unpack('f', stream.read(4))
        self.z, = struct.unpack('f', stream.read(4))
