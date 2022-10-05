from renderer.data import ReplayData


class ConsumableManager:
    def __init__(self, replay_data: list[ReplayData]) -> None:
        self.replay_data = replay_data
        self.active_consumables = {}

    def update(self, game_time: int):
        consumables = {}

        for replay_data in self.replay_data:
            consumables.update(replay_data.events[game_time].evt_consumable)

        for consumable in consumables.values():
            for player_consumable in consumable:
                acs = self.active_consumables.setdefault(
                    player_consumable.ship_id, {}
                )
                acs[player_consumable.consumable_id] = round(
                    player_consumable.duration
                )

    def tick(self):
        for apcs in list(self.active_consumables.keys()):
            for apc in list(self.active_consumables[apcs]):
                if self.active_consumables[apcs][apc] > 0:
                    self.active_consumables[apcs][apc] -= 1
                else:
                    self.active_consumables[apcs].pop(apc)

                    if not self.active_consumables[apcs]:
                        self.active_consumables.pop(apcs)
