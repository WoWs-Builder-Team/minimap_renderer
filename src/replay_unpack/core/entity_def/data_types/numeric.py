# coding=utf-8
import struct
from io import BytesIO

from lxml import etree

from .base import DataType


class _NumericType(DataType):
    STRUCT_TYPE = None
    PYTHON_TYPE = None

    def __init__(self, header_size=1):
        assert None not in [self.STRUCT_TYPE, self.PYTHON_TYPE], \
            "You must define STRUCT_TYPE and PYTHON_TYPE first"
        super().__init__(header_size=header_size)

    def _get_value_from_stream(self, stream: BytesIO, header_size: int):
        return struct.unpack(self.STRUCT_TYPE, stream.read(self._DATA_SIZE))[0]

    def _get_default_value_from_section(self, section: etree.ElementBase):
        return self.PYTHON_TYPE(section.text.strip())


class Int8(_NumericType):
    """
    INT8 
    — Size (bytes): 1 
    — Range: From: -128 To: 127
    Signed 8-bit integer.
    """
    PYTHON_TYPE = int
    STRUCT_TYPE = 'b'
    _DATA_SIZE = 1


class Int16(_NumericType):
    """
    INT16 
    — Size (bytes): 2 
    — Range: From: -8,768 To: 8,767
    Signed 16-bit integer.
    """
    PYTHON_TYPE = int
    STRUCT_TYPE = 'h'
    _DATA_SIZE = 2


class Int32(_NumericType):
    """
    INT8 
    — Size (bytes): 4 
    — Range: From: -2,147,483,648 To: 2,147,483,647
    Signed 8-bit integer.
    """
    PYTHON_TYPE = int
    STRUCT_TYPE = 'i'
    _DATA_SIZE = 4


class Int64(_NumericType):
    """
    INT64 
    — Size (bytes): 8 
    — Range: From: -9,223,372,036,854,775,808 To: 9,223,372,036,854,775,807
    Signed 64-bit integer.
    """
    PYTHON_TYPE = int
    STRUCT_TYPE = 'q'
    _DATA_SIZE = 8


class UInt8(_NumericType):
    """
    UINT8 
    — Size(bytes): 1 
    — Range: From: 0 To: 255
    Unsigned 8-bit integer.
    """
    PYTHON_TYPE = int
    STRUCT_TYPE = 'B'
    _DATA_SIZE = 1

    def _get_default_value_from_section(self, section: etree.ElementBase):
        # INT8 is alias for BOOL which has different DEFAULT values
        if section.text.strip().lower() in ['true', 'false']:
            return section.text.strip().lower() == 'true'
        return super(UInt8, self)._get_default_value_from_section(section)


class UInt16(_NumericType):
    """
    UINT16 
    — Size(bytes): 2 
    — Range: From: 0 To: 65,535
    Unsigned 16-bit integer.
    """
    PYTHON_TYPE = int
    STRUCT_TYPE = 'H'
    _DATA_SIZE = 2


class UInt32(_NumericType):
    """
    UINT8 
    — Size(bytes): 4 
    — Range: From: 0 To: 4,294,967,295
    Unsigned 8-bit integer.
    """
    PYTHON_TYPE = int
    STRUCT_TYPE = 'I'
    _DATA_SIZE = 4


class UInt64(_NumericType):
    """
    UINT64 
    — Size(bytes): 8 
    — Range: From: 0 To: 18,446,744,073,709,551,615
    Unsigned 64-bit integer.
    """
    PYTHON_TYPE = int
    STRUCT_TYPE = 'Q'
    _DATA_SIZE = 8


class Float32(_NumericType):
    """
    FLOAT32
    — Size (bytes): 4
    IEEE 8-bit floating-point number.
    """
    PYTHON_TYPE = float
    STRUCT_TYPE = 'f'
    _DATA_SIZE = 4


class Float64(_NumericType):
    """
    FLOAT64 
    — Size (bytes): 8
    IEEE 64-bit floating-point number.
    """
    PYTHON_TYPE = float
    STRUCT_TYPE = 'd'
    _DATA_SIZE = 8
