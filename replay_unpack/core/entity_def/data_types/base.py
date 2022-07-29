# coding=utf-8
import logging
from io import BytesIO

from lxml import etree


class DataType:
    DEFAULT_VALUE = None
    _DATA_SIZE = None

    def __init__(self, header_size=1):
        self._nullable = False
        self._header_size = header_size

        assert self.get_size_in_bytes() is not None, \
            "You must define DATA_SIZE variable " \
            "or get_size_in_bytes method %s" % self.__class__.__name__

    @classmethod
    def from_section(cls, alias, section, header_size):
        return cls(header_size=header_size)

    def get_default_value(self, default: etree.ElementBase):
        """
        This method sets the default value associated with this type.
        """
        if default is None:
            return self.DEFAULT_VALUE
        logging.debug('Parsing default value for %s', self.__class__.__name__)
        return self._get_default_value_from_section(default)

    def create_from_stream(self, stream: BytesIO, header_size: int = 1):
        return self._get_value_from_stream(stream, header_size)

    def _get_value_from_stream(self, stream: BytesIO, header_size: int):
        raise NotImplementedError()

    def write_to_stream(self, stream: BytesIO):
        raise RuntimeError("Not supported for now")

    def _get_default_value_from_section(self, value: etree.ElementBase):
        raise NotImplementedError

    def get_size_in_bytes(self):
        return self._DATA_SIZE

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)
