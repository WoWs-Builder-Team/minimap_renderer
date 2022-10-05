# coding=utf-8
import struct

from replay_unpack.core import PrettyPrintObjectMixin


class EntityControl(PrettyPrintObjectMixin):
    def __init__(self, stream):
        self.entityId, self.isControled = struct.unpack('ib', stream.read(5))
