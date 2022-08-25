# coding=utf-8
from io import BytesIO
from typing import List, Dict, Tuple

from lxml import etree

from .base_definition import BaseDataObjectDef
from .data_types import DataType, Alias, INFINITY

DEFAULT_HEADER_SIZE = 1


class MethodArgument:
    def __init__(self, type_: DataType, name=None):
        self.name = name
        self.type = type_

    def __repr__(self):
        if self.name:
            return '%s: %s' % (self.name, self.type)
        return 'unknown: %s' % self.type


class EntityMethod:

    def __init__(self, name, arguments: List[MethodArgument], header_size: int = DEFAULT_HEADER_SIZE):
        self._name = name or None
        self._arguments = arguments
        self._variable_header_size = header_size

    def get_name(self):
        return self._name

    def get_size_in_bytes(self):
        size = sum(i.type.get_size_in_bytes() for i in self._arguments)
        if size >= INFINITY:
            return INFINITY + self._variable_header_size
        return size + self._variable_header_size

    def _get_header_size_from_section(self, section: etree.ElementBase):
        """
        E.g.
        <onEnterPreBattle>
            <Arg>BLOB</Arg>
            <VariableLengthHeaderSize>
                <WarnLevel>none</WarnLevel>
            </VariableLengthHeaderSize>
        </onEnterPreBattle>
        """
        if section.find('VariableLengthHeaderSize'):
            return int(section.find('VariableLengthHeaderSize').text.strip())
        return None

    @classmethod
    def from_section(cls, section: etree.ElementBase, alias):
        args = []
        if section.find('Args') is not None:
            for item in section.find('Args'):
                args.append(MethodArgument(
                    name=item.tag, type_=alias.get_data_type_from_section(item)))
        else:
            for item in section.findall('Arg'):
                args.append(MethodArgument(
                    type_=alias.get_data_type_from_section(item)))

        header_section = section.find('VariableLengthHeaderSize')
        try:
            header_size = int(header_section.text.strip())
        except (ValueError, AttributeError):
            header_size = DEFAULT_HEADER_SIZE

        return cls(section.tag, list(args), header_size)

    def create_from_stream(self, stream: BytesIO) -> Tuple[List, Dict[str, object]]:
        unpacked_args = []
        unpacked_kwargs = {}
        for arg in self._arguments:
            unpacked = arg.type.create_from_stream(stream, self._variable_header_size)
            if arg.name is None:
                unpacked_args.append(unpacked)
            else:
                unpacked_kwargs[arg.name] = unpacked

        return unpacked_args, unpacked_kwargs

    def __repr__(self):
        return "{name} ({args})".format(
            name=self._name, args=self._arguments)


class MethodDescriptions:
    def __init__(self):
        self._internal_index = []
        self._methods_by_name: Dict[EntityMethod] = {}

    def parse(self, section: etree.ElementBase, alias):
        for method in section:
            obj = EntityMethod.from_section(method, alias)
            if obj.get_name() in self._methods_by_name:
                continue
            self._internal_index.append(obj)
            self._methods_by_name[obj.get_name()] = obj

    def get_exposed_index_map(self) -> List[EntityMethod]:
        array = self._internal_index[:]
        array.sort(key=lambda i: i.get_size_in_bytes())
        return array


class EntityDef(BaseDataObjectDef):
    """
    This class is used to describe a type of entity. It describes all properties
    and methods of an entity type, as well as other information related to
    object instantiation, level-of-detail etc. It is normally created on startup
    when the entities.xml file is parsed.
    """

    def __init__(self, base_dir: str, name: str, section: etree.ElementBase, alias: Alias):
        self._name = name
        self._cell_methods = MethodDescriptions()
        self._base_methods = MethodDescriptions()
        self._client_methods = MethodDescriptions()

        super(EntityDef, self).__init__(base_dir, alias)

        self._parse_section(section)

    def get_name(self):
        return self._name

    def cell(self):
        return self._cell_methods

    def base(self):
        return self._base_methods

    def client(self):
        return self._client_methods

    def properties(self):
        return self._properties

    def volatiles(self):
        return self._volatile

    def _parse_cell_methods(self, section: etree.ElementBase):
        if section is None:
            return
        self._cell_methods.parse(section, self._alias)

    def _parse_base_methods(self, section: etree.ElementBase):
        if section is None:
            return
        self._base_methods.parse(section, self._alias)

    def _parse_client_methods(self, section: etree.ElementBase):
        if section is None:
            return
        self._client_methods.parse(section, self._alias)

    def _parse_section(self, section: etree.ElementBase):
        super(EntityDef, self)._parse_section(section)
        self._parse_client_methods(section.find("ClientMethods"))
        self._parse_cell_methods(section.find("CellMethods"))
        self._parse_base_methods(section.find("BaseMethods"))
