import sys, os
from collections import defaultdict
import importlib

sys.path.insert(0, 'src')
from replay_parser import ReplayParser
from replay_unpack.core.entity import Entity
from replay_unpack.clients.wows.player import ReplayPlayer

const_mod = importlib.import_module('replay_unpack.clients.wows.versions.15_7_0.constants')
DEATH_TYPES = const_mod.DEATH_TYPES

# Collect all events for all vehicles
events_by_vehicle = defaultdict(list)
current_time = 0.0

def set_time(t):
    global current_time
    current_time = t

orig_process = ReplayPlayer._process_packet
def patched_process(self, packet, t: float):
    set_time(t)
    return orig_process(self, packet, t)
ReplayPlayer._process_packet = patched_process

def on_dmg(vehicle, damages):
    events_by_vehicle[vehicle.id].append({
        'time': current_time,
        'type': 'direct_damage',
        'damages': damages
    })
Entity.subscribe_method_call('Vehicle', 'receiveDamagesOnShip', on_dmg)

def on_burning_flags(vehicle, flags):
    events_by_vehicle[vehicle.id].append({
        'time': current_time,
        'type': 'burning_flags',
        'flags': flags
    })
Entity.subscribe_property_change('Vehicle', 'burningFlags', on_burning_flags)

def on_health(vehicle, health):
    events_by_vehicle[vehicle.id].append({
        'time': current_time,
        'type': 'health',
        'health': health
    })
Entity.subscribe_property_change('Vehicle', 'health', on_health)

def on_regen(vehicle, health):
    events_by_vehicle[vehicle.id].append({
        'time': current_time,
        'type': 'regenerated_health',
        'health': health
    })
Entity.subscribe_property_change('Vehicle', 'regeneratedHealth', on_regen)

def on_death(avatar, killed, fragger, dtype):
    events_by_vehicle[killed].append({
        'time': current_time,
        'type': 'death',
        'fragger': fragger,
        'dtype': dtype,
        'name': DEATH_TYPES.get(dtype, {}).get('name', str(dtype))
    })
Entity.subscribe_method_call('Avatar', 'receiveVehicleDeath', on_death)

with open(r'F:\[工具]\minimap_renderer\20260907_123622_PWSB010-Thor_58_RidgeNew.wowsreplay', 'rb') as f:
    p = ReplayParser(f)
    info = p.get_info()

hidden = info['hidden']
rd = hidden['replay_data']
players = rd.player_info

# Let's inspect Case 1: Ramming (440987 and 440995) around t=360-375s
print("================== CASE 1: RAMMING (440987 vs 440995) ==================")
for vid in [440987, 440995]:
    p_info = players.get(rd.player_info[players[rd.owner_id].id].id) # just get player
    p_obj = [p for p in players.values() if p.ship_id == vid][0]
    print(f"\nEvents for {p_obj.name} (ship_id {vid}, max_hp {p_obj.max_health}):")
    for ev in events_by_vehicle[vid]:
        if 360.0 <= ev['time'] <= 375.0:
            print(f"  t={ev['time']:.2f}s: {ev}")

# Let's inspect Case 2: Flooding kill on 441019 around t=470-495s
print("\n================== CASE 2: FLOOD KILL (441019) ==================")
p_obj = [p for p in players.values() if p.ship_id == 441019][0]
print(f"Events for {p_obj.name} (ship_id 441019, max_hp {p_obj.max_health}):")
for ev in events_by_vehicle[441019]:
    if 460.0 <= ev['time'] <= 495.0:
        print(f"  t={ev['time']:.2f}s: {ev}")

# Let's inspect Case 3: Fire kill on Owner (441005) around t=650-700s
print("\n================== CASE 3: BURNING KILL (441005 - Owner) ==================")
p_obj = [p for p in players.values() if p.ship_id == 441005][0]
print(f"Events for {p_obj.name} (ship_id 441005, max_hp {p_obj.max_health}):")
for ev in events_by_vehicle[441005]:
    if 660.0 <= ev['time'] <= 700.0:
        print(f"  t={ev['time']:.2f}s: {ev}")
