# coding=utf-8
from abc import ABCMeta, abstractmethod
from typing import Dict

from replay_unpack.core.entity import Entity


class IBattleController(metaclass=ABCMeta):
    """
    Proxy to real battle controller of given version
    """

    @property
    @abstractmethod
    def entities(self) -> Dict[int, Entity]:
        pass

    @abstractmethod
    def create_entity(self, entity: Entity) -> None:
        pass

    @abstractmethod
    def destroy_entity(self, entity: Entity) -> None:
        pass

    @abstractmethod
    def on_player_enter_world(self, entity_id: int):
        pass

    @property
    @abstractmethod
    def map(self) -> str:
        pass

    @map.setter
    def map(self, value: str):
        pass

    def get_info(self) -> Dict:
        pass
