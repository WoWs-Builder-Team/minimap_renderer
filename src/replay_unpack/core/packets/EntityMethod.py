# coding=utf-8
import struct

from replay_unpack.core import PrettyPrintObjectMixin
from replay_unpack.core.network.types import BinaryStream


class EntityMethod(PrettyPrintObjectMixin):
    """
    Fires when servers requests client to call
    entity's method with some arguments
    """
    __slots__ = (
        'entityId',
        'messageId',
        'data',
    )

    def __init__(self, stream):
        self.entityId, = struct.unpack('I', stream.read(4))
        self.messageId, = struct.unpack('I', stream.read(4))

        self.data = BinaryStream(stream)
