# coding=utf-8
import logging
from copy import copy
from enum import Enum
from io import BytesIO
from typing import Callable, Dict, List, Tuple

from replay_unpack.core.entity_def import EntityDef
from replay_unpack.core.entity_def import EntityFlags


class Entity:
    class Type(Enum):
        """
        Enum which represents all possible entity variations
        """

        CLIENT = 1
        CELL = 2
        BASE = 4

    _methods_subscriptions = {}  # type: Dict[Type, List[Callable]]
    _properties_subscriptions = {}  # type: Dict[Type, List[Callable]]
    _nested_properties_subscription = {}

    def __init__(self, id_: int, spec: EntityDef):
        self.id = id_
        self._spec = spec
        self._methods = spec.client().get_exposed_index_map()

        # we had to store properties values because network protocol
        # supports updating them partly (lists and dicts)
        self.properties = {"client": {}, "cell": {}, "base": {}}

        # position, yaw, pitch, roll
        self.volatiles = copy(spec.volatiles())

        self.client_properties = spec.properties().get_properties_by_flags(
            EntityFlags.ALL_CLIENTS
            | EntityFlags.BASE_AND_CLIENT
            | EntityFlags.OTHER_CLIENTS
            | EntityFlags.OWN_CLIENT
            | EntityFlags.CELL_PUBLIC_AND_OWN
            | EntityFlags.ALL_CLIENTS,
            exposed_index=True,
        )
        self.client_properties_internal = spec.properties().get_properties_by_flags(
            EntityFlags.ALL_CLIENTS
            |
            # not used for some reason
            # EntityFlags.BASE_AND_CLIENT |
            EntityFlags.OTHER_CLIENTS
            | EntityFlags.OWN_CLIENT
            | EntityFlags.CELL_PUBLIC_AND_OWN
            | EntityFlags.ALL_CLIENTS
        )
        self.cell_properties = spec.properties().get_properties_by_flags(
            EntityFlags.CELL_PUBLIC_AND_OWN
            | EntityFlags.CELL_PUBLIC
            # | EntityFlags.CELL_PRIVATE
        )
        self.base_properties = spec.properties().get_properties_by_flags(
            # EntityFlags.BASE |
            EntityFlags.BASE_AND_CLIENT
        )

        self._is_on_aoi = True

    @property
    def is_on_aoi(self):
        return self._is_on_aoi

    @is_on_aoi.setter
    def is_on_aoi(self, value):
        self._is_on_aoi = value

    @classmethod
    def subscribe_method_call(
        cls, entity_name: str, method_name: str, func: Callable
    ):
        """
        Add callbacks that should be triggered when given method called
        """
        if method_name not in cls._methods_subscriptions:
            cls._methods_subscriptions[entity_name + "_" + method_name] = []
        cls._methods_subscriptions[entity_name + "_" + method_name].append(
            func
        )

    @classmethod
    def subscribe_property_change(
        cls, entity_name: str, prop_name: str, func: Callable
    ):
        """
        Add callbacks that should be triggered when given method called
        """
        prop_hash = entity_name + "_" + prop_name
        if prop_name not in cls._properties_subscriptions:
            cls._properties_subscriptions[prop_hash] = []
        cls._properties_subscriptions[prop_hash].append(func)

    def call_client_method(self, exposed_index: int, payload: BytesIO):
        method = self._methods[exposed_index]
        logging.debug("calling %s method %s", self._spec.get_name(), method)
        method_hash = self._spec.get_name() + "_" + method.get_name()
        # print(method_hash)
        subscriptions = Entity._methods_subscriptions.get(method_hash, [])
        # if method.get_name() not in ["onCheckGamePing", "onCheckCellPing"]:
        #     print(method_hash)
        if not subscriptions:
            return

        args, kwargs = method.create_from_stream(payload)
        for func in subscriptions:
            try:
                func(self, *args, **kwargs)
            except TypeError as e:
                logging.error(
                    "Failed to call %s with args %s "
                    "and kwargs %s, problem: '%s'",
                    func,
                    args,
                    kwargs,
                    e,
                )
                raise

    def set_client_property(self, exposed_index, payload: BytesIO):
        logging.debug(
            "requested property %s of entity %s",
            exposed_index,
            self._spec.get_name(),
        )
        prop = self.client_properties[exposed_index]
        logging.debug(
            "setting %s client property %s", self._spec.get_name(), prop
        )

        value = prop.create_from_stream(payload)
        self.properties["client"][prop.get_name()] = value
        prop_hash = f"{self._spec.get_name()}_{prop.get_name()}"
        subscriptions = Entity._properties_subscriptions.get(prop_hash, [])

        if not subscriptions:
            return
        for func in subscriptions:
            try:
                func(self, value)
            except TypeError as e:
                raise

    @classmethod
    def subscribe_nested_property_change(
        cls, entity_name: str, prop_path: str, func: Callable
    ):

        prop_hash = entity_name + "_" + prop_path
        if prop_path not in cls._nested_properties_subscription:
            cls._nested_properties_subscription[prop_hash] = []
        cls._nested_properties_subscription[prop_hash].append(func)

    def set_client_nested_property(self, prop_path: list, obj):
        prop_hash = f"{self.get_name()}_{'.'.join(map(str, prop_path))}"

        for phash, funcs in Entity._nested_properties_subscription.items():
            if phash in prop_hash:
                for func in funcs:
                    func(self, obj)

    def set_client_property_internal(self, internal_index, payload: BytesIO):
        logging.debug(
            "requested property %s of entity %s",
            internal_index,
            self._spec.get_name(),
        )
        prop = self.client_properties_internal[internal_index]
        logging.debug(
            "setting %s client property %s", self._spec.get_name(), prop
        )
        self.properties["client"][prop.get_name()] = prop.create_from_stream(
            payload
        )

    def set_cell_property(self, internal_index, payload: BytesIO):
        prop = self.cell_properties[internal_index]
        logging.debug(
            "setting %s cell property %s", self._spec.get_name(), prop
        )
        self.properties["cell"][prop.get_name()] = prop.create_from_stream(
            payload
        )

    def set_base_property(self, internal_index, payload: BytesIO):
        prop = self.base_properties[internal_index]
        logging.debug(
            "setting %s base property %s", self._spec.get_name(), prop
        )
        self.properties["base"][prop.get_name()] = prop.create_from_stream(
            payload
        )

    def get_name(self):
        return self._spec.get_name()

    @property
    def position(self) -> Tuple[float, float, float]:
        try:
            return self.volatiles["position"]
        except KeyError:
            raise RuntimeError(
                "Entity %s does not have volatile %s"
                % (self.get_name(), "position")
            )

    @position.setter
    def position(self, value: Tuple[float, float, float]):
        self.volatiles["position"] = value

    @property
    def yaw(self) -> float:
        try:
            return self.volatiles["yaw"]
        except KeyError:
            raise RuntimeError(
                "Entity %s does not have volatile %s"
                % (self.get_name(), "yaw")
            )

    @yaw.setter
    def yaw(self, value: float):
        self.volatiles["yaw"] = value

    @property
    def pitch(self) -> float:
        try:
            return self.volatiles["pitch"]
        except KeyError:
            raise RuntimeError(
                "Entity %s does not have volatile %s"
                % (self.get_name(), "pitch")
            )

    @pitch.setter
    def pitch(self, value: float):
        self.volatiles["pitch"] = value

    @property
    def roll(self) -> float:
        try:
            return self.volatiles["roll"]
        except KeyError:
            raise RuntimeError(
                "Entity %s does not have volatile %s"
                % (self.get_name(), "roll")
            )

    @roll.setter
    def roll(self, value: float):
        self.volatiles["roll"] = value

    def __repr__(self):
        return "{}<{}>".format(self._spec.get_name(), self.id)
