import struct


class Version:
    def __init__(self, stream):
        self._size, = struct.unpack('i', stream.read(4))
        self.version = stream.read(self._size).decode('utf8')