# coding=utf-8

from replay_unpack.core import IBattleController
from replay_unpack.core.entity import Entity


class BattleController(IBattleController):

    def __init__(self):
        self._entities = {}

        self._map = None
        self._player_id = None
        self._tracerts = []
        # just for test
        Entity.subscribe_method_call('Avatar', 'showTracer', lambda *args: self._tracerts.append(args[1:]))

    @property
    def entities(self):
        return self._entities

    @property
    def battle_logic(self):
        return next(e for e in self._entities.values() if e.get_name() == 'BattleLogic')

    def create_entity(self, entity: Entity):
        self._entities[entity.id] = entity

    def destroy_entity(self, entity: Entity):
        self._entities.pop(entity.id)

    def on_player_enter_world(self, entity_id: int):
        self._player_id = entity_id

    def get_info(self):
        return dict(
            map=self.map,
            player_id=self._player_id,
            tracerts=self._tracerts
        )

    @property
    def map(self):
        return self._map

    @map.setter
    def map(self, value):
        self._map = value.lstrip('spaces/')
