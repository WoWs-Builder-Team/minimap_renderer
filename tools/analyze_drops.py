import sys, os
from collections import defaultdict
import importlib

sys.path.insert(0, 'src')
from replay_parser import ReplayParser
from replay_unpack.core.entity import Entity
from replay_unpack.clients.wows.player import ReplayPlayer

const_mod = importlib.import_module('replay_unpack.clients.wows.versions.15_8_0.constants')
DEATH_TYPES = const_mod.DEATH_TYPES

# Track detailed state of each vehicle at every timestamp
vehicle_states = defaultdict(lambda: {
    'hp': 0.0,
    'max_hp': 0.0,
    'burn_flags': 0,
    'regen_hp': 0.0,
    'is_alive': True
})

hp_drop_events = [] # (time, vid, hp_before, hp_after, drop, has_direct, direct_dmg_info, burn_flags)
direct_damages_at_time = defaultdict(list)

orig_process = ReplayPlayer._process_packet
t_curr = 0.0
def patched(self, packet, t: float):
    global t_curr
    t_curr = t
    return orig_process(self, packet, t)
ReplayPlayer._process_packet = patched

def on_dmg(v, d):
    for item in d:
        direct_damages_at_time[(round(t_curr, 2), v.id)].append(item)
Entity.subscribe_method_call('Vehicle', 'receiveDamagesOnShip', on_dmg)

def on_burn(v, f):
    vehicle_states[v.id]['burn_flags'] = f
Entity.subscribe_property_change('Vehicle', 'burningFlags', on_burn)

def on_regen(v, h):
    vehicle_states[v.id]['regen_hp'] = h
Entity.subscribe_property_change('Vehicle', 'regeneratedHealth', on_regen)

def on_hp(v, h):
    st = vehicle_states[v.id]
    prev_hp = st['hp']
    st['hp'] = h
    if prev_hp > 0 and h < prev_hp:
        drop = prev_hp - h
        t_key = round(t_curr, 2)
        # Check direct damages within 0.1s
        dmgs = []
        for dt_off in [0.0, -0.01, 0.01, -0.02, 0.02, -0.05, 0.05, -0.1, 0.1]:
            k = (round(t_curr + dt_off, 2), v.id)
            if k in direct_damages_at_time:
                dmgs.extend(direct_damages_at_time[k])
        
        hp_drop_events.append({
            'time': t_curr,
            'vid': v.id,
            'prev_hp': prev_hp,
            'new_hp': h,
            'drop': drop,
            'has_direct': len(dmgs) > 0,
            'dmgs': dmgs,
            'burn_flags': st['burn_flags'],
            'regen_hp': st['regen_hp']
        })
Entity.subscribe_property_change('Vehicle', 'health', on_hp)

with open(r'F:\[工具]\minimap_renderer\20260907_123622_PWSB010-Thor_58_RidgeNew.wowsreplay', 'rb') as f:
    p = ReplayParser(f)
    info = p.get_info()

hidden = info['hidden']
rd = hidden['replay_data']
players = rd.player_info

# Analyze hp_drop_events without direct damage
non_direct_drops = [e for e in hp_drop_events if not e['has_direct']]
print(f"Total HP drop events: {len(hp_drop_events)}")
print(f"HP drop events with direct damage: {len(hp_drop_events) - len(non_direct_drops)}")
print(f"HP drop events WITHOUT direct damage: {len(non_direct_drops)}")

# Group non-direct drops by burn_flags
burn_drops = [e for e in non_direct_drops if e['burn_flags'] > 0]
no_burn_drops = [e for e in non_direct_drops if e['burn_flags'] == 0]

print(f"\nNon-direct drops with burningFlags > 0 (Fire DoT): {len(burn_drops)}, total drop: {sum(e['drop'] for e in burn_drops):.1f}")
print(f"Non-direct drops with burningFlags == 0: {len(no_burn_drops)}, total drop: {sum(e['drop'] for e in no_burn_drops):.1f}")

# Inspect non-direct drops with burningFlags == 0
print("\nSample non-direct drops with burningFlags == 0:")
for e in no_burn_drops[:30]:
    p_name = players[rd.player_info[players[rd.owner_id].id].id].name # default
    for p in players.values():
        if p.ship_id == e['vid']:
            p_name = p.name
    print(f"  t={e['time']:.2f}s | {p_name} ({e['vid']}) lost {e['drop']:.1f} HP (from {e['prev_hp']:.1f} to {e['new_hp']:.1f})")
