# coding=utf-8
import struct

from replay_unpack.core import PrettyPrintObjectMixin


class Matrix4(PrettyPrintObjectMixin):
    __slots__ = [
        'm11', 'm12', 'm13', 'm14',
        'm21', 'm22', 'm23', 'm24',
        'm31', 'm32', 'm33', 'm34',
        'm41', 'm42', 'm43', 'm44',
    ]

    def __init__(self, stream):
        self.m11, = struct.unpack('f', stream.read(4))
        self.m12, = struct.unpack('f', stream.read(4))
        self.m13, = struct.unpack('f', stream.read(4))
        self.m14, = struct.unpack('f', stream.read(4))
        self.m21, = struct.unpack('f', stream.read(4))
        self.m22, = struct.unpack('f', stream.read(4))
        self.m23, = struct.unpack('f', stream.read(4))
        self.m24, = struct.unpack('f', stream.read(4))
        self.m31, = struct.unpack('f', stream.read(4))
        self.m32, = struct.unpack('f', stream.read(4))
        self.m33, = struct.unpack('f', stream.read(4))
        self.m34, = struct.unpack('f', stream.read(4))
        self.m41, = struct.unpack('f', stream.read(4))
        self.m42, = struct.unpack('f', stream.read(4))
        self.m43, = struct.unpack('f', stream.read(4))
        self.m44, = struct.unpack('f', stream.read(4))
