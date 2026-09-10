import sys, os
from collections import defaultdict

sys.path.insert(0, 'src')
from replay_parser import ReplayParser
from replay_unpack.core.entity import Entity
import importlib
const_mod = importlib.import_module('replay_unpack.clients.wows.versions.15_8_0.constants')
DEATH_TYPES = const_mod.DEATH_TYPES

# Collect all relevant events with timestamps
timeline = []
current_time = 0.0

def set_time(t):
    global current_time
    current_time = t

# Track receiveDamagesOnShip
def on_dmg(vehicle, damages):
    timeline.append({
        'time': current_time,
        'type': 'direct_damage',
        'victim': vehicle.id,
        'damages': damages
    })
Entity.subscribe_method_call('Vehicle', 'receiveDamagesOnShip', on_dmg)

# Track receiveHitLocationStateChange
def on_hl_change(vehicle, hl_id, state_packed):
    timeline.append({
        'time': current_time,
        'type': 'hl_change',
        'victim': vehicle.id,
        'hl_id': hl_id,
        'state_packed': state_packed
    })
Entity.subscribe_method_call('Vehicle', 'receiveHitLocationStateChange', on_hl_change)

# Track burningFlags
def on_burning_flags(vehicle, flags):
    timeline.append({
        'time': current_time,
        'type': 'burning_flags',
        'victim': vehicle.id,
        'flags': flags
    })
Entity.subscribe_property_change('Vehicle', 'burningFlags', on_burning_flags)

# Track health
def on_health(vehicle, health):
    timeline.append({
        'time': current_time,
        'type': 'health',
        'victim': vehicle.id,
        'health': health
    })
Entity.subscribe_property_change('Vehicle', 'health', on_health)

# Track regeneratedHealth
def on_regen(vehicle, health):
    timeline.append({
        'time': current_time,
        'type': 'regenerated_health',
        'victim': vehicle.id,
        'health': health
    })
Entity.subscribe_property_change('Vehicle', 'regeneratedHealth', on_regen)

# Track deaths
def on_death(avatar, killed, fragger, dtype):
    timeline.append({
        'time': current_time,
        'type': 'death',
        'killed': killed,
        'fragger': fragger,
        'dtype': dtype,
        'death_name': DEATH_TYPES.get(dtype, {}).get('name', str(dtype))
    })
Entity.subscribe_method_call('Avatar', 'receiveVehicleDeath', on_death)

# Patch ReplayPlayer._process_packet to record packet time
from replay_unpack.clients.wows.player import ReplayPlayer
orig_process = ReplayPlayer._process_packet
def patched_process(self, packet, t: float):
    set_time(t)
    return orig_process(self, packet, t)
ReplayPlayer._process_packet = patched_process

with open(r'F:\[工具]\minimap_renderer\20260907_123622_PWSB010-Thor_58_RidgeNew.wowsreplay', 'rb') as f:
    p = ReplayParser(f)
    info = p.get_info()

hidden = info['hidden']
rd = hidden['replay_data']
players = rd.player_info
v_names = {p.ship_id: f"{p.name} ({p.ship_id})" for p in players.values()}

print(f"Total recorded timeline events: {len(timeline)}")

# 1. Inspect hl_change events: what hl_id values exist?
hl_ids = defaultdict(int)
for e in timeline:
    if e['type'] == 'hl_change':
        hl_ids[e['hl_id']] += 1
print(f"Hit location IDs encountered: {dict(hl_ids)}")

# 2. Inspect death events
print("\n=== DEATH EVENTS ===")
for e in timeline:
    if e['type'] == 'death':
        k_name = v_names.get(e['killed'], str(e['killed']))
        f_name = v_names.get(e['fragger'], str(e['fragger']))
        print(f"t={e['time']:.1f}s | {k_name} killed by {f_name} via {e['death_name']} (type {e['dtype']})")
