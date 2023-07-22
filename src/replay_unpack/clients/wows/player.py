# coding=utf-8
import logging
import struct
from io import BytesIO

from replay_unpack.core import Entity
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
    PlayerPosition,
    Version,
    PACKETS_MAPPING, PACKETS_MAPPING_12_6_0,
)


class ReplayPlayer(ControlledPlayerBase):
    def _get_definitions(self, version):
        try:
            return get_definitions("_".join(version[:4]))
        except RuntimeError:
            return get_definitions("_".join(version[:3]))

    def _get_controller(self, version):
        try:
            return get_controller("_".join(version[:4]))
        except RuntimeError:
            return get_controller("_".join(version[:3]))

    def _get_packets_mapping(self):
        # Since gameclient version 12.6.0, some packets have had their indices changed.
        if self._version >= (12, 6, 0, 0) or self._version > (12, 6, 0):
            return PACKETS_MAPPING_12_6_0
        else:
            return PACKETS_MAPPING

    def _process_packet(self, packet, t: float):
        self._battle_controller.set_packet_time(t)

        if isinstance(packet, Version):
            self._battle_controller._version = packet.version

        if isinstance(packet, Map):
            logging.debug("Welcome to map %s: %s", packet.name, packet.arenaId)
            self._battle_controller.map = packet.name

        elif isinstance(packet, BasePlayerCreate):
            # I'm not sure what is the order of cell/base/client player creation
            if packet.entityId in self._battle_controller.entities:
                base_player = self._battle_controller.entities[packet.entityId]
            else:
                base_player = Entity(
                    id_=packet.entityId,
                    spec=self._definitions.get_entity_def_by_name("Avatar"),
                )

            # base is internal, so props are stored in order of xml file
            io = BytesIO(packet.value.value)
            for index, prop in enumerate(base_player.base_properties):
                base_player.set_base_property(index, io)

            self._battle_controller.create_entity(base_player)
            self._battle_controller.on_player_enter_world(packet.entityId)

        elif isinstance(packet, CellPlayerCreate):
            # I'm not sure what is the order of cell/base/client player creation
            if packet.entityId in self._battle_controller.entities:
                cell_player = self._battle_controller.entities[packet.entityId]
            else:
                cell_player = Entity(
                    id_=packet.entityId,
                    spec=self._definitions.get_entity_def_by_name("Avatar"),
                )

            # cell is internal, so props are stored in order of xml file
            io = packet.value.io()
            for index, prop in enumerate(
                cell_player.client_properties_internal
            ):
                cell_player.set_client_property_internal(index, io)
            # TODO: why this assert fails?
            # assert io.read() == b''
            self._battle_controller.create_entity(cell_player)

        elif isinstance(packet, EntityEnter):
            self._battle_controller.entities[packet.entityId].is_in_aoi = True

        elif isinstance(packet, EntityLeave):
            self._battle_controller.entities[packet.entityId].is_in_aoi = False
            self._battle_controller.leave_entity(packet.entityId)

        elif isinstance(packet, EntityCreate):
            entity = Entity(
                id_=packet.entityID,
                spec=self._definitions.get_entity_def_by_index(packet.type),
            )

            entity.position = packet.position

            values = packet.state.io()
            (values_count,) = struct.unpack("B", values.read(1))
            for i in range(values_count):
                k = values.read(1)
                (idx,) = struct.unpack("B", k)
                entity.set_client_property(idx, values)
            assert values.read() == b""
            self._battle_controller.create_entity(entity)

        elif isinstance(packet, Position):
            self._battle_controller.entities[
                packet.entityId
            ].position = packet.position
            self._battle_controller.entities[packet.entityId].yaw = packet.yaw
            self._battle_controller.entities[
                packet.entityId
            ].pitch = packet.pitch
            self._battle_controller.entities[
                packet.entityId
            ].roll = packet.roll

        elif isinstance(packet, PlayerPosition):
            try:
                # Entity at ID 1 is the primary one's position being updated
                # Avatar-only packets have no position until death, and
                # are linked to a vehicle. After death they have no ID for a
                # Vehicle anymore, and a position instead.
                # Before death only "Vehicle in ID 1" packets have a position.

                if packet.entityId2 != (0,):
                    # This serves to link the positions of the two entities
                    # where the position of entity 1 is set by wherever entity 2
                    # is, rather than by the position field.
                    # e.g. Assigning the Avatar the position of the Vehicle
                    master_entity = self._battle_controller.entities[
                        packet.entityId2
                    ]
                    slave_entity = self._battle_controller.entities[
                        packet.entityId1
                    ]

                    slave_entity.position = master_entity.position
                    slave_entity.yaw = master_entity.yaw
                    slave_entity.pitch = master_entity.pitch
                    slave_entity.roll = master_entity.roll

                elif packet.entityId1 != 0 and packet.entityId2 == 0:
                    # This is a regular update for entity 1, without entity 2
                    e = self._battle_controller.entities[packet.entityId1]

                    e.position = packet.position
                    e.yaw = packet.yaw
                    e.pitch = packet.pitch
                    e.roll = packet.roll

                else:
                    # Shouldn't hit this case, with no primary OR secondary entity
                    pass

            except KeyError as e:
                # entity not yet created
                pass

        elif isinstance(packet, EntityMethod):
            entity = self._battle_controller.entities[packet.entityId]
            entity.call_client_method(packet.messageId, packet.data.io())

        elif isinstance(packet, EntityProperty):
            entity = self._battle_controller.entities[packet.objectID]
            entity.set_client_property(packet.messageId, packet.data.io())

        elif isinstance(packet, NestedProperty):
            e = self._battle_controller.entities[packet.entity_id]

            logging.debug("")
            logging.debug(
                "nested property request for id=%s isSlice=%s packet=%s",
                e.id,
                packet.is_slice,
                packet.payload.hex(),
            )
            packet.read_and_apply(e)
