import sys, os
from collections import defaultdict
import importlib

sys.path.insert(0, 'src')
from replay_parser import ReplayParser
from replay_unpack.core.entity import Entity
from replay_unpack.clients.wows.player import ReplayPlayer

const_mod = importlib.import_module('replay_unpack.clients.wows.versions.15_7_0.constants')
DEATH_TYPES = const_mod.DEATH_TYPES

# Let's track everything:
# - burningFlags changes: (t, vid, flags)
# - health changes: (t, vid, hp)
# - direct damage: (t, victim, attacker, dmg)
# - deaths: (t, killed, fragger, dtype)
# - shots fired / received (receiveArtilleryShots, receiveTorpedoes)

all_burn_events = defaultdict(list)
all_hp_events = defaultdict(list)
all_dmg_events = []
all_deaths = []

orig_process = ReplayPlayer._process_packet
t_curr = 0.0
def patched(self, packet, t: float):
    global t_curr
    t_curr = t
    return orig_process(self, packet, t)
ReplayPlayer._process_packet = patched

def on_burn(v, f):
    all_burn_events[v.id].append((t_curr, f))
Entity.subscribe_property_change('Vehicle', 'burningFlags', on_burn)

def on_hp(v, h):
    all_hp_events[v.id].append((t_curr, h))
Entity.subscribe_property_change('Vehicle', 'health', on_hp)

def on_dmg(v, d):
    for item in d:
        all_dmg_events.append((t_curr, v.id, item['vehicleID'], item['damage']))
Entity.subscribe_method_call('Vehicle', 'receiveDamagesOnShip', on_dmg)

def on_death(a, k, f, d):
    all_deaths.append((t_curr, k, f, d, DEATH_TYPES.get(d, {}).get('name', str(d))))
Entity.subscribe_method_call('Avatar', 'receiveVehicleDeath', on_death)

with open(r'F:\[工具]\minimap_renderer\20260907_123622_PWSB010-Thor_58_RidgeNew.wowsreplay', 'rb') as f:
    p = ReplayParser(f)
    info = p.get_info()

hidden = info['hidden']
rd = hidden['replay_data']
players = rd.player_info

# Let's inspect each ship's burning intervals
print("=== BURNING INTERVALS ===")
for p in sorted(players.values(), key=lambda x: x.ship_id):
    vid = p.ship_id
    b_list = all_burn_events[vid]
    if b_list:
        print(f"Ship {vid} ({p.name}, {p.ship_params_id}): {len(b_list)} burn flag changes")
        intervals = []
        cur_flags = 0
        start_t = 0.0
        for t, f in b_list:
            if cur_flags == 0 and f > 0:
                start_t = t
                cur_flags = f
            elif cur_flags > 0 and f == 0:
                intervals.append((start_t, t, cur_flags))
                cur_flags = 0
            elif cur_flags > 0 and f > 0:
                intervals.append((start_t, t, cur_flags))
                start_t = t
                cur_flags = f
        if cur_flags > 0:
            intervals.append((start_t, 9999.0, cur_flags))
        for s, e, f in intervals:
            print(f"    t={s:.1f}s - {e:.1f}s: flags={bin(f)} (duration {e-s:.1f}s)")
