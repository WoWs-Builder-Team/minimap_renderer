# coding=utf-8
import os
from typing import Dict

from lxml import etree

from .constants import ENTITIES_DEFS_PATH
from .data_types import Alias
from .entity_description import EntityDef


class Definitions:
    def __init__(self, base_dir):
        self._alias = Alias(base_dir)

        self._entity_defs_by_name: Dict[str, EntityDef] = {}
        self._entity_defs_by_index: Dict[int, EntityDef] = {}
        self._parse(base_dir)

    def get_entity_def_by_name(self, name):
        return self._entity_defs_by_name[name]

    def get_entity_def_by_index(self, index):
        # bigworld counts entities from 1
        return self._entity_defs_by_index[index - 1]

    def _parse_entities(self, base_dir: str, entities: etree.ElementBase):
        for index, entity_section in enumerate(entities):
            path = os.path.join(base_dir, ENTITIES_DEFS_PATH, entity_section.tag + '.def')
            section = etree.parse(path, parser=etree.XMLParser(remove_comments=True))
            entity_def = EntityDef(base_dir, entity_section.tag, section, self._alias)

            self._entity_defs_by_name[entity_section.tag] = entity_def
            self._entity_defs_by_index[index] = entity_def

    def _parse(self, base_dir):
        tree = etree.parse(os.path.join(base_dir, 'scripts/entities.xml'),
                           parser=etree.XMLParser(remove_comments=True))
        root = tree.getroot()
        self._parse_entities(base_dir, root.find('ClientServerEntities'))
