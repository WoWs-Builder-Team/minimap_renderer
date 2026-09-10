import sys, os
from collections import defaultdict
import importlib

sys.path.insert(0, 'src')
from replay_parser import ReplayParser
from replay_unpack.core.entity import Entity
from replay_unpack.clients.wows.player import ReplayPlayer

const_mod = importlib.import_module('replay_unpack.clients.wows.versions.15_8_0.constants')
DEATH_TYPES = const_mod.DEATH_TYPES

# Track full timeline of events
t_curr = 0.0
orig_process = ReplayPlayer._process_packet
def patched(self, packet, t: float):
    global t_curr
    t_curr = t
    return orig_process(self, packet, t)
ReplayPlayer._process_packet = patched

vehicle_history = defaultdict(list)
direct_damages = defaultdict(list)
deaths = []

def on_hp(v, h):
    vehicle_history[v.id].append((t_curr, 'hp', h))
Entity.subscribe_property_change('Vehicle', 'health', on_hp)

def on_burn(v, f):
    vehicle_history[v.id].append((t_curr, 'burn', f))
Entity.subscribe_property_change('Vehicle', 'burningFlags', on_burn)

def on_regen(v, h):
    vehicle_history[v.id].append((t_curr, 'regen', h))
Entity.subscribe_property_change('Vehicle', 'regeneratedHealth', on_regen)

def on_dmg(v, d):
    for item in d:
        direct_damages[v.id].append((t_curr, item['vehicleID'], item['damage']))
Entity.subscribe_method_call('Vehicle', 'receiveDamagesOnShip', on_dmg)

def on_death(a, k, f, d):
    deaths.append((t_curr, k, f, d, DEATH_TYPES.get(d, {}).get('name', str(d))))
Entity.subscribe_method_call('Avatar', 'receiveVehicleDeath', on_death)

with open(r'F:\[工具]\minimap_renderer\20260907_123622_PWSB010-Thor_58_RidgeNew.wowsreplay', 'rb') as f:
    p = ReplayParser(f)
    info = p.get_info()

hidden = info['hidden']
players = hidden['replay_data'].player_info
v_names = {p.ship_id: p.name for p in players.values()}

# Let's inspect each ship's total HP loss and correlate with direct damage
print("=== DETAILED SHIP HP BREAKDOWN ===")
for p in sorted(players.values(), key=lambda x: (x.team_id, x.ship_id)):
    vid = p.ship_id
    mhp = p.max_health
    
    # Calculate HP timeline
    h_events = [ev for ev in vehicle_history[vid] if ev[1] == 'hp']
    b_events = [ev for ev in vehicle_history[vid] if ev[1] == 'burn']
    d_events = direct_damages[vid]
    
    tot_direct_taken = sum(d[2] for d in d_events)
    
    # Trace step-by-step HP drops
    drops = []
    cur_burn = 0
    cur_hp = mhp
    
    # Merge hp and burn events by time
    merged = sorted(vehicle_history[vid], key=lambda x: x[0])
    burn_st = 0
    hp_st = mhp
    
    fire_drops = 0.0
    non_fire_drops = 0.0
    
    for t, k, val in merged:
        if k == 'burn':
            burn_st = val
        elif k == 'hp':
            if hp_st > val:
                drop = hp_st - val
                if burn_st > 0:
                    fire_drops += drop
                else:
                    non_fire_drops += drop
            hp_st = val
            
    print(f"\n{p.name:20s} ({vid}, Team {p.team_id}) MaxHP={mhp:7.1f}:")
    print(f"  Direct taken:     {tot_direct_taken:9.1f}")
    print(f"  Fire state drops: {fire_drops:9.1f}")
    print(f"  Non-fire drops:   {non_fire_drops:9.1f}")
    print(f"  Total drops:      {fire_drops + non_fire_drops:9.1f}")
    print(f"  Delta vs Direct:  {(fire_drops + non_fire_drops) - tot_direct_taken:9.1f}")
