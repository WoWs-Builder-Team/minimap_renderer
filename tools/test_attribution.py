import sys, os
from collections import defaultdict
import importlib

sys.path.insert(0, 'src')
from replay_parser import ReplayParser
from replay_unpack.core.entity import Entity
from replay_unpack.clients.wows.player import ReplayPlayer

const_mod = importlib.import_module('replay_unpack.clients.wows.versions.15_7_0.constants')
DEATH_TYPES = const_mod.DEATH_TYPES

# Track full timeline of events
t_curr = 0.0
orig_process = ReplayPlayer._process_packet
def patched(self, packet, t: float):
    global t_curr
    t_curr = t
    return orig_process(self, packet, t)
ReplayPlayer._process_packet = patched

# Data structures
all_events = [] # (t, type, vid, data)

def on_hp(v, h):
    all_events.append((t_curr, 'hp', v.id, h))
Entity.subscribe_property_change('Vehicle', 'health', on_hp)

def on_burn(v, f):
    all_events.append((t_curr, 'burn', v.id, f))
Entity.subscribe_property_change('Vehicle', 'burningFlags', on_burn)

def on_dmg(v, d):
    for item in d:
        all_events.append((t_curr, 'direct', v.id, (item['vehicleID'], item['damage'])))
Entity.subscribe_method_call('Vehicle', 'receiveDamagesOnShip', on_dmg)

def on_death(a, k, f, d):
    all_events.append((t_curr, 'death', k, (f, d, DEATH_TYPES.get(d, {}).get('name', str(d)))))
Entity.subscribe_method_call('Avatar', 'receiveVehicleDeath', on_death)

with open(r'F:\[工具]\minimap_renderer\20260907_123622_PWSB010-Thor_58_RidgeNew.wowsreplay', 'rb') as f:
    p = ReplayParser(f)
    info = p.get_info()

hidden = info['hidden']
players = hidden['replay_data'].player_info
v_names = {p.ship_id: p.name for p in players.values()}

# Sort all events chronologically
all_events.sort(key=lambda x: (x[0], 0 if x[1] == 'burn' else 1 if x[1] == 'direct' else 2 if x[1] == 'hp' else 3))

# Trace fire ignitions and who caused them
# Fire ignition: when burn bit flips from 0 to 1
# Attacker: look at direct hits within [-2.5s, +0.5s]
fire_attributions = {} # (vid, bit_mask) -> attacker_id

# Let's run a first pass to find fire ignitions
burn_states = defaultdict(int)
for t, etype, vid, data in all_events:
    if etype == 'burn':
        old_f = burn_states[vid]
        new_f = data
        if new_f > old_f:
            new_bits = new_f & ~old_f
            # Find recent direct attackers
            candidates = []
            for item in all_events:
                if item[1] == 'direct' and item[2] == vid and abs(item[0] - t) <= 2.5:
                    att_id, dmg = item[3]
                    candidates.append((abs(item[0] - t), att_id, dmg))
            candidates.sort(key=lambda x: x[0])
            if candidates:
                best_att = candidates[0][1]
                fire_attributions[(vid, t)] = best_att
        burn_states[vid] = new_f

print(f"Total fire ignitions attributed: {len(fire_attributions)}")
for (vid, t), att in sorted(fire_attributions.items(), key=lambda x: x[0][1]):
    v_n = v_names.get(vid, str(vid))
    a_n = v_names.get(att, str(att))
    print(f"  t={t:6.1f}s | {v_n:18s} fire set by {a_n:18s}")
