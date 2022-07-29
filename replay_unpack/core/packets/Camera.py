# coding=utf-8
import struct

from replay_unpack.core import PrettyPrintObjectMixin
from replay_unpack.core.network.types import Vector3


class Camera(PrettyPrintObjectMixin):
    def __init__(self, stream):
        try:
            self.unknown1, = struct.unpack('f', stream.read(4))
            self.unknown2, = struct.unpack('f', stream.read(4))
            self.unknown3, = struct.unpack('f', stream.read(4))

            self.unknown4, = struct.unpack('f', stream.read(4))

            self.unknown5, = struct.unpack('f', stream.read(4))
            self.unknown6, = struct.unpack('f', stream.read(4))
            self.unknown7, = struct.unpack('f', stream.read(4))

            self.fov, = struct.unpack('f', stream.read(4))
            self.position = Vector3(stream)
            self.direction = Vector3(stream)
        except:
            pass
