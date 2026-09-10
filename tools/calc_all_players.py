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

all_events.sort(key=lambda x: (x[0], 0 if x[1] == 'burn' else 1 if x[1] == 'direct' else 2 if x[1] == 'hp' else 3))

# Step 1: Attribute each fire ignition to an attacker
# Store: (victim_id, start_time, end_time, attacker_id)
burn_intervals = []
cur_burn = defaultdict(lambda: {'flags': 0, 'start_t': 0.0, 'attacker': None})

for t, etype, vid, data in all_events:
    if etype == 'burn':
        old_f = cur_burn[vid]['flags']
        new_f = data
        if new_f > old_f: # New fire ignited
            # Find candidate attacker
            candidates = []
            for item in all_events:
                if item[1] == 'direct' and item[2] == vid and abs(item[0] - t) <= 2.5:
                    att_id, dmg = item[3]
                    candidates.append((abs(item[0] - t), att_id, dmg))
            candidates.sort(key=lambda x: x[0])
            att = candidates[0][1] if candidates else None
            
            if cur_burn[vid]['flags'] > 0:
                # Close previous interval
                burn_intervals.append({
                    'vid': vid,
                    'start_t': cur_burn[vid]['start_t'],
                    'end_t': t,
                    'attacker': cur_burn[vid]['attacker'],
                    'flags': cur_burn[vid]['flags']
                })
            cur_burn[vid] = {'flags': new_f, 'start_t': t, 'attacker': att}
        elif new_f < old_f: # Fire extinguished
            if cur_burn[vid]['flags'] > 0:
                burn_intervals.append({
                    'vid': vid,
                    'start_t': cur_burn[vid]['start_t'],
                    'end_t': t,
                    'attacker': cur_burn[vid]['attacker'],
                    'flags': cur_burn[vid]['flags']
                })
            cur_burn[vid] = {'flags': new_f, 'start_t': t, 'attacker': None}

# Close any remaining burn intervals
for vid, st in cur_burn.items():
    if st['flags'] > 0:
        burn_intervals.append({
            'vid': vid,
            'start_t': st['start_t'],
            'end_t': 9999.0,
            'attacker': st['attacker'],
            'flags': st['flags']
        })

# Step 2: Track deaths and killers
death_info = {}
for t, etype, vid, data in all_events:
    if etype == 'death':
        fragger, dtype, dname = data
        death_info[vid] = {
            'time': t,
            'fragger': fragger,
            'dtype': dtype,
            'dname': dname
        }

# Step 3: Detailed HP drop accounting
# Damage categories per player:
# - direct_dealt
# - fire_dealt
# - flood_dealt
# - ram_dealt
# - unspotted_death_dealt (fragger credited for kill on unspotted ship)

damage_dealt = defaultdict(lambda: {
    'direct': 0.0,
    'fire': 0.0,
    'flood': 0.0,
    'ram': 0.0,
    'unspotted_death': 0.0
})

damage_taken = defaultdict(lambda: {
    'direct': 0.0,
    'fire': 0.0,
    'flood': 0.0,
    'ram': 0.0,
    'unspotted_death': 0.0
})

# Direct damage can be directly credited from `direct` events:
for t, etype, vid, data in all_events:
    if etype == 'direct':
        att_id, dmg = data
        damage_dealt[att_id]['direct'] += dmg
        damage_taken[vid]['direct'] += dmg

# Now process non-direct HP drops
# For each ship, track HP timeline and subtract direct damage to find non-direct drops
for p in players.values():
    vid = p.ship_id
    mhp = p.max_health
    
    # Check if this ship died to RAM
    is_ram_death = (vid in death_info and death_info[vid]['dtype'] == 7)
    # Check if this ship died to FLOOD
    is_flood_death = (vid in death_info and death_info[vid]['dtype'] == 9)
    # Check if this ship died to BURNING
    is_burn_death = (vid in death_info and death_info[vid]['dtype'] == 6)
    
    # Calculate drops
    cur_h = mhp
    v_events = [ev for ev in all_events if ev[2] == vid]
    
    for item in v_events:
        t, etype, _, data = item
        if etype == 'hp':
            if cur_h > data:
                drop = cur_h - data
                
                # Check if there is a direct damage event near this time
                recent_direct = [ev for ev in all_events if ev[1] == 'direct' and ev[2] == vid and abs(ev[0] - t) <= 1.2]
                
                # If this is the final drop to 0.0 upon death:
                if data == 0.0 and vid in death_info and abs(death_info[vid]['time'] - t) <= 2.0:
                    d_item = death_info[vid]
                    killer = d_item['fragger']
                    dtype = d_item['dtype']
                    
                    if dtype == 7: # RAM
                        damage_dealt[killer]['ram'] += drop
                        damage_taken[vid]['ram'] += drop
                    elif dtype == 9: # FLOOD
                        damage_dealt[killer]['flood'] += drop
                        damage_taken[vid]['flood'] += drop
                    elif dtype == 6: # BURNING
                        damage_dealt[killer]['fire'] += drop
                        damage_taken[vid]['fire'] += drop
                    else:
                        # Direct weapon kill (AP/HE/TBOMB) while drop had no direct record (e.g. Preussen outside AoI)
                        # Check how much direct damage was recorded near here
                        dir_sum = sum(ev[3][1] for ev in recent_direct)
                        unaccounted = max(0.0, drop - dir_sum)
                        if unaccounted > 500.0: # Significant unrecorded HP loss
                            damage_dealt[killer]['unspotted_death'] += unaccounted
                            damage_taken[vid]['unspotted_death'] += unaccounted
                else:
                    # Intermediate drop
                    # Is ship currently burning?
                    active_burn = [b for b in burn_intervals if b['vid'] == vid and b['start_t'] <= t <= b['end_t']]
                    if active_burn and not recent_direct:
                        att = active_burn[0]['attacker']
                        if att:
                            damage_dealt[att]['fire'] += drop
                            damage_taken[vid]['fire'] += drop
                    elif is_flood_death and not recent_direct:
                        killer = death_info[vid]['fragger']
                        damage_dealt[killer]['flood'] += drop
                        damage_taken[vid]['flood'] += drop
            cur_h = data

print("=== CORRECTED DAMAGE DEALT SUMMARY (ALL 24 PLAYERS) ===")
print(f"{'Team':4s} | {'ShipID':8s} | {'Player Name':20s} | {'Direct':10s} | {'Fire DoT':9s} | {'Flood DoT':9s} | {'Ramming':9s} | {'AoI/Unspot':10s} | {'Total Damage':12s}")
print("-" * 115)

for p in sorted(players.values(), key=lambda x: (x.team_id, x.ship_id)):
    vid = p.ship_id
    d = damage_dealt[vid]
    tot = d['direct'] + d['fire'] + d['flood'] + d['ram'] + d['unspotted_death']
    print(f"{p.team_id:4d} | {vid:8d} | {p.name[:20]:20s} | {d['direct']:10.1f} | {d['fire']:9.1f} | {d['flood']:9.1f} | {d['ram']:9.1f} | {d['unspotted_death']:10.1f} | {tot:12.1f}")
