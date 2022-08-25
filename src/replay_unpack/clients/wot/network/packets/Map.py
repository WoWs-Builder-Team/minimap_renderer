# coding=utf-8
import struct

from replay_unpack.core.pretty_print_mixin import PrettyPrintObjectMixin


class Map(PrettyPrintObjectMixin):
    def __init__(self, stream):
        self.spaceId, = struct.unpack('i', stream.read(4))
        self.arenaId, = struct.unpack('i', stream.read(4))

        _name_size, = struct.unpack('b', stream.read(1))
        self.name = stream.read(_name_size).decode('utf-8')
