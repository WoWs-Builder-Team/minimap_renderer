# coding=utf-8
import os
import struct

from replay_unpack.core import PrettyPrintObjectMixin


class Map(PrettyPrintObjectMixin):
    def __init__(self, stream):
        self.spaceId, = struct.unpack('i', stream.read(4))
        self.arenaId, = struct.unpack('q', stream.read(8))
        # something new added in 0.7.9, just skip it
        _name_size, = struct.unpack('i', stream.read(4))
        pos = stream.tell()
        stream.seek(0, os.SEEK_END)
        s_len = stream.tell()
        stream.seek(pos)

        if pos + _name_size + 16 * 4 != s_len - 1:
            stream.read(16 * 8 + 4)
            _name_size, = struct.unpack('i', stream.read(4))
        self.name = stream.read(_name_size).decode('utf-8')
