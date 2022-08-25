# coding=utf-8
import struct
from io import BytesIO as StringIO

from replay_unpack.core import PrettyPrintObjectMixin


class BinaryStream(PrettyPrintObjectMixin):
    __slots__ = (
        '_length',
        'value'
    )

    def __init__(self, stream):
        self._length, = struct.unpack('I', stream.read(4))
        self.value = stream.read(self._length)

    def io(self):
        return StringIO(self.value)
