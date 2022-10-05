# coding=utf-8
import os
from typing import Dict

from lxml import etree

from .base import DataType
from .constants import INFINITY
from .math import (
    Vector2,
    Vector3,
    Vector4,
)
from .numeric import (
    Int8,
    Int16,
    Int32,
    Int64,
    UInt8,
    UInt16,
    UInt32,
    UInt64,
    Float32,
    Float64,
)
from .other import (
    Python,
    Blob,
    String,
    FixedDict,
    Array,
    Mailbox,
    UserType)


class Alias:
    SIMPLE_TYPES = {
        'BLOB': Blob,
        'STRING': String,
        'UNICODE_STRING': String,
        'FLOAT': Float32,
        'FLOAT32': Float32,
        'FLOAT64': Float64,
        'INT8': Int8,
        'INT16': Int16,
        'INT32': Int32,
        'INT64': Int64,
        'UINT8': UInt8,
        'UINT16': UInt16,
        'UINT32': UInt32,
        'UINT64': UInt64,
        'VECTOR2': Vector2,
        'VECTOR3': Vector3,
        'VECTOR4': Vector4,
        'MAILBOX': Mailbox,
        'PYTHON': Python,
        'FIXED_DICT': FixedDict,
        'ARRAY': Array,
        'TUPLE': Array,  # almost the same,
        'USER_TYPE': UserType,  # almost the same
    }

    def __init__(self, base_dir: str):
        self._mapping: Dict[str, DataType] = {}
        self._alias: Dict[str, etree.ElementBase] = {}
        self._initialize(base_dir)

    def get_data_type_from_section(self, section: etree.ElementBase, header_size=1) -> DataType:
        type_name = section.text.strip()

        if type_name in self._alias:
            return self.get_data_type_from_section(self._alias[type_name], header_size)
        elif type_name in self.SIMPLE_TYPES:
            return self.SIMPLE_TYPES[type_name].from_section(self, section, header_size)
        else:
            raise RuntimeError("%s is unknown" % type_name)

    def _initialize(self, base_dir):
        alias_path = os.path.join(base_dir, 'scripts/entity_defs/alias.xml')
        if not os.path.exists(alias_path):
            raise RuntimeError("Not supported version")

        with open(alias_path, 'rb') as f:
            xml = etree.parse(f, parser=etree.XMLParser(encoding='utf8',
                remove_comments=True))
            for item in xml.getroot():
                self._alias[item.tag] = item

        for key, section in self._alias.items():
            _type = self.get_data_type_from_section(section)
            self._mapping[key] = _type
