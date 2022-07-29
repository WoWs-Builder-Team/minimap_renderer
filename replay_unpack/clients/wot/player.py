# coding=utf-8
import logging
import struct

from replay_unpack.core import (
    Entity
)
from replay_unpack.core.network.player import ControlledPlayerBase
from .helper import get_definitions, get_controller
from .network.packets import (
    Map,
    BasePlayerCreate,
    CellPlayerCreate,
    EntityCreate,
    Position,
    EntityMethod,
    EntityProperty,
    NestedProperty,
    EntityEnter,
    EntityLeave,
    PACKETS_MAPPING
)


class ReplayPlayer(ControlledPlayerBase):

    def _get_definitions(self, version):
        return get_definitions(version)

    def _get_controller(self, version):
        return get_controller(version)

    def _get_packets_mapping(self):
        return PACKETS_MAPPING

    def _process_packet(self, packet):

        if isinstance(packet, Map):
            logging.debug('Welcome to map %s: %s', packet.name, packet.arenaId)
            self._battle_controller.map = packet.name

        elif isinstance(packet, BasePlayerCreate):
            # I'm not sure what is the order of cell/base/client player creation
            if packet.entityId in self._battle_controller.entities:
                base_player = self._battle_controller.entities[packet.entityId]
            else:
                base_player = Entity(id_=packet.entityId,
                                     spec=self._definitions.get_entity_def_by_name('Avatar'))

            # base is internal, so props are stored in order of xml file
            # io = BytesIO(packet.value.value)
            # for index, prop in enumerate(base_player.base_properties):
            #     base_player.set_base_property(index, io)

            self._battle_controller.create_entity(base_player)
            self._battle_controller.on_player_enter_world(packet.entityId)

        elif isinstance(packet, CellPlayerCreate):
            # I'm not sure what is the order of cell/base/client player creation
            if packet.entityId in self._battle_controller.entities:
                cell_player = self._battle_controller.entities[packet.entityId]
            else:
                cell_player = Entity(id_=packet.entityId,
                                     spec=self._definitions.get_entity_def_by_name('Avatar'))

            # cell is internal, so props are stored in order of xml file
            io = packet.value.io()
            for index, prop in enumerate(cell_player.client_properties_internal):
                cell_player.set_client_property_internal(index, io)
            # TODO: why this assert fails?
            # assert io.read() == b''
            self._battle_controller.create_entity(cell_player)

        elif isinstance(packet, EntityEnter):
            self._battle_controller.entities[packet.entityId].is_in_aoi = True

        elif isinstance(packet, EntityLeave):
            self._battle_controller.entities[packet.entityId].is_in_aoi = False

        elif isinstance(packet, EntityCreate):
            entity = Entity(
                id_=packet.entityID,
                spec=self._definitions.get_entity_def_by_index(packet.type))

            values = packet.state.io()
            values_count, = struct.unpack('B', values.read(1))
            for i in range(values_count):
                k = values.read(1)
                idx, = struct.unpack('B', k)
                entity.set_client_property(idx, values)
            assert values.read() == b''
            self._battle_controller.create_entity(entity)

        elif isinstance(packet, Position):
            self._battle_controller.entities[packet.entityId].position = packet.position
            self._battle_controller.entities[packet.entityId].yaw = packet.yaw
            self._battle_controller.entities[packet.entityId].pitch = packet.pitch
            self._battle_controller.entities[packet.entityId].roll = packet.roll

        elif isinstance(packet, EntityMethod):
            entity = self._battle_controller.entities[packet.entityId]
            entity.call_client_method(packet.messageId, packet.data.io())

        elif isinstance(packet, EntityProperty):
            entity = self._battle_controller.entities[packet.objectID]
            entity.set_client_property(packet.messageId, packet.data.io())

        elif isinstance(packet, NestedProperty):
            e = self._battle_controller.entities[packet.entity_id]

            logging.debug('')
            logging.debug('nested property request for id=%s isSlice=%s packet=%s',
                          e.id, packet.is_slice, packet.payload.hex())
            packet.read_and_apply(e)
