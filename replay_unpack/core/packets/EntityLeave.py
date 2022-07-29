# coding=utf-8
import struct

from replay_unpack.core import PrettyPrintObjectMixin


class EntityLeave(PrettyPrintObjectMixin):
    """
    Fires when entity leaves AOI and stops
    receiving updates from server
    """

    def __init__(self, stream):
        self.entityId, = struct.unpack('i', stream.read(4))
