# coding=utf-8
import logging
import struct
from io import BytesIO

from replay_unpack.core import Entity
from replay_unpack.core import PrettyPrintObjectMixin
from replay_unpack.core.entity_def.bit_reader import BitReader
from replay_unpack.core.entity_def.data_types.nested_types import (
    PyFixedDict,
    PyFixedList,
)


class NestedProperty(PrettyPrintObjectMixin):
    def __init__(self, stream):
        (self.entity_id,) = struct.unpack("I", stream.read(4))
        self.is_slice = struct.unpack("b", stream.read(1))[0] == 1
        (self.payload_size,) = struct.unpack("b", stream.read(1))

        self.u = stream.read(3)  # unknown
        self.payload = stream.read()
        assert len(self.payload) == self.payload_size

    def read_and_apply(self, entity):
        bit_reader = BitReader(self.payload)
        obj = entity
        field = None

        while bit_reader.get(1) and obj:
            l = (
                len(obj.client_properties)
                if isinstance(obj, Entity)
                else len(obj)
            )
            max_bits = BitReader.bits_required(l)
            property_id = bit_reader.get(max_bits)
            if hasattr(obj, "get_field_name_for_index"):
                field = obj.get_field_name_for_index(property_id)
                obj = obj[field]
            elif isinstance(obj, Entity):
                field = obj.client_properties[property_id].get_name()
                # FIXME: what about cell and base properties?
                obj = obj.properties["client"][field]
            else:
                raise NotImplementedError
            logging.debug("next path item: %s(%s)", field, property_id)

        logging.debug("object: %s %s", obj, type(obj))

        if isinstance(obj, PyFixedDict):
            assert self.is_slice is False
            max_bits = BitReader.bits_required(len(obj))
            index1 = bit_reader.get(max_bits)

            field = obj.get_field_name_for_index(index1)
            logging.debug("old obj[%s] = %s", field, obj[field])
            obj[field] = obj.get_field_type_for_index(
                index1
            ).create_from_stream(BytesIO(bit_reader.get_rest()))
            logging.debug("new obj[%s] = %s", field, obj[field])

        elif isinstance(obj, PyFixedList):
            if self.is_slice:
                max_bits = BitReader.bits_required(len(obj) + 1)
            else:
                max_bits = BitReader.bits_required(len(obj))
            index1 = bit_reader.get(max_bits)
            logging.debug("Bits per array index: %s", max_bits)
            logging.debug("List index: %s", index1)
            if self.is_slice:
                index2 = bit_reader.get(max_bits)
                logging.debug("Slice index: %s", index2)

            rest = bit_reader.get_rest()
            if not rest:
                logging.debug(
                    "empty response, bytes read %s", bit_reader.bytes_read
                )
                if self.is_slice:
                    logging.debug("removing element %s", obj[index1:index2])
                    obj[index1:index2] = []
                else:
                    obj[index1] = None
                return
            io = BytesIO(rest)
            new_elements = []
            # read elements unless io is empty, sizes should match
            while io.tell() != len(rest):
                t = obj.get_element_type().create_from_stream(io)
                logging.debug(
                    "Bytes left in io: %s of %s", io.tell(), len(rest)
                )
                new_elements.append(t)
            assert io.tell() == len(rest)
            logging.debug("old list object: %s", obj)

            if self.is_slice:
                logging.debug(
                    "replacing %s:%s with %s", index1, index2, new_elements
                )
                obj[index1:index2] = new_elements
            else:
                logging.debug("setting %s with %s", index1, new_elements[0])
                obj[index1] = new_elements[0]
            logging.debug("new list object: %s", obj)
            entity.set_client_nested_property(field, obj)
        else:
            raise NotImplementedError(type(obj))
