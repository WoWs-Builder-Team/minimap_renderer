# coding=utf-8
"""
This file provides the implementation of the UserDataObjectDescription class.
"""
import os
from io import BytesIO
from typing import List, Dict

from lxml import etree

from .constants import ENTITIES_DEFS_PATH, EntityFlags
from .data_types import Alias, DataType, INFINITY


class BaseDataObjectDef:
    def __init__(self, base_dir: str, alias: Alias):
        self._properties = PropertiesDescriptions()
        self._volatile = {}
        self._alias = alias
        self._base_dir = base_dir

    def _parse_implements(self, implements_list: etree.ElementBase):
        """
        This method parses a data section for the properties and methods associated
        with this user data object description.
        """
        if implements_list is None:
            return

        for it in implements_list:
            path = os.path.join(self._base_dir, ENTITIES_DEFS_PATH, 'interfaces', it.text.strip() + '.def')
            parsed = etree.parse(path, parser=etree.XMLParser(
                remove_comments=True,
                # use recover to ignore bad xsi sections
                recover=True))
            section = parsed.getroot()
            self._parse_section(section)

    def _parse_properties(self, props_list: etree.ElementBase):
        """
        This method parses a data section for the properties associated with this
        entity description.
        """
        if props_list is None:
            return
        self._properties.parse(props_list, self._alias)

    def _parse_volatile(self, props_list: etree.ElementBase):
        """
        Some properties are updated more often than others,
        and almost all entities have a set of properties that
        need to be handled specially due to this. These properties
        are called volatile properties, and are pre-defined
        by the BigWorld engine.
        <position/> | <position> float </position>
        <yaw/> | <yaw> float </yaw>
        <pitch/> | <pitch> float </pitch>
        <roll/> | <roll> float </roll>
        """
        if props_list is None:
            return

        for item in props_list:
            if item.tag == 'position':
                self._volatile['position'] = (0, 0, 0)
            elif item.tag in ['yaw', 'pitch', 'roll']:
                self._volatile[item.tag] = 0.0

    def _parse_section(self, section: etree.ElementBase):
        self._parse_implements(section.find("Implements"))
        self._parse_properties(section.find("Properties"))
        self._parse_volatile(section.find("Volatile"))


class Property:

    def __init__(self, name: str, type_: DataType, flags: str, default: etree.ElementBase = None):
        self._name = name
        self._type = type_
        self._default = type_.get_default_value(default)
        self._flags = getattr(EntityFlags, flags)

    def get_name(self):
        return self._name

    def get_size_in_bytes(self):
        return min(self._type.get_size_in_bytes(), INFINITY)

    def get_default_value(self):
        return self._default

    @classmethod
    def from_section(cls, section: etree.ElementBase, alias):
        """
        Create property object from xml section like following
        <ownShipId>
            <Type>ENTITY_ID</Type>
            <Flags>ALL_CLIENTS</Flags>
            <Default>0</Default>
        </ownShipId>
        """

        type_ = alias.get_data_type_from_section(section.find('Type'))
        default = section.find('Default')
        flags = section.find('Flags').text.strip()

        return cls(section.tag, type_, flags=flags, default=default)

    def create_from_stream(self, stream: BytesIO):
        return self._type.create_from_stream(stream)

    def __repr__(self):
        return "{name} ({args})".format(
            name=self._name, args=self._type)


class PropertiesDescriptions:
    def __init__(self):
        self._internal_index: List[Property] = []
        self._props_by_name: Dict[str, Property] = {}

    def parse(self, section: etree.ElementBase, alias) -> None:
        for prop in section:
            obj = Property.from_section(prop, alias)
            # when same-named properties are in interface
            # and in definition, game client uses last one
            if obj.get_name() in self._props_by_name:
                self._internal_index.remove(self._props_by_name[obj.get_name()])
                self._props_by_name.pop(obj.get_name())
            self._internal_index.append(obj)
            self._props_by_name[obj.get_name()] = obj

    def get_properties_by_flags(self, flags: int, exposed_index=False) -> List[Property]:
        """
        Get list of properties that match given flags
        Use exposed_index=True to sort properties by payload size
        """
        props = []
        for prop in self._internal_index:
            if not prop._flags & flags:
                continue
            props.append(prop)

        # client-server index, ordered props by payload size
        if exposed_index:
            props.sort(key=lambda i: i.get_size_in_bytes())
        return props
