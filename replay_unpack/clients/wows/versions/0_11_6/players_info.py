# coding=utf-8
from .constants import (
    id_property_map,
    id_property_map_bots,
    id_property_map_observer
)


class PlayerType:
    PLAYER = 1
    BOT = 2
    OBSERVER = 3


class PlayersInfo(object):
    def __init__(self):
        self._players = {}

    def _convert_to_dict(self, player_info, player_type):
        # type: (list[tuple], int) -> dict
        if player_type == PlayerType.PLAYER:
            property_map = id_property_map
        elif player_type == PlayerType.BOT:
            property_map = id_property_map_bots
        elif player_type == PlayerType.OBSERVER:
            property_map = id_property_map_observer
        else:
            raise RuntimeError('Unknown player')

        player_dict = dict()
        for key, value in player_info:
            player_dict[property_map[key]] = value
        return player_dict

    def create_or_update_players(self, players_info, players_type=PlayerType.PLAYER):
        for player_info in players_info:
            player_dict = self._convert_to_dict(player_info, players_type)

            self._players.setdefault(player_dict['id'], {}).update(player_dict)

    def get_info(self):
        return self._players

    def __repr__(self):
        return str(self._players)
