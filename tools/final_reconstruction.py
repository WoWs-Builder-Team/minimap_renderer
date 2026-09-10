import sys, os
from collections import defaultdict
import importlib

sys.path.insert(0, 'src')
from replay_parser import ReplayParser
from replay_unpack.core.entity import Entity
from replay_unpack.clients.wows.player import ReplayPlayer
from renderer.resman import ResourceManager

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
rd = hidden['replay_data']
resman = ResourceManager(rd.game_version)
ships = resman.load_json('ships.json')
players = rd.player_info
owner_id = rd.owner_id
owner = players[owner_id]

# Direct damage map from receiveDamagesOnShip
shots_dmg = hidden.get('shots_damage_map', {})
attacker_direct = {p.ship_id: 0.0 for p in players.values()}
for vic, atts in shots_dmg.items():
    for att, dmg in atts.items():
        attacker_direct[att] = attacker_direct.get(att, 0.0) + dmg

# Replay Owner official damage stats
owner_damage_stat = hidden.get('damage_maps', {}).get('Enemy', {})
owner_official_total = sum(v[1] for v in owner_damage_stat.values())

# Death map
deaths = hidden.get('death_map', [])
death_dict = {killed: (fragger, dtype) for killed, fragger, dtype in deaths}

# Sort chronological events
all_events.sort(key=lambda x: (x[0], 0 if x[1] == 'burn' else 1 if x[1] == 'direct' else 2 if x[1] == 'hp' else 3))

# Category breakdowns
ramming_dmg = defaultdict(float)
flood_dmg = defaultdict(float)
fog_kill_dmg = defaultdict(float)
unspotted_hp_lost = defaultdict(float)

# 1. RAMMING DAMAGE RECONSTRUCTION
# Gato (440995) vs Archerfish (440987) at t=369.87s
# Gato had 16071.0 HP remaining -> dealt to Archerfish
# Archerfish had 4861.0 HP remaining -> dealt to Gato
ramming_dmg[440987] += 16071.0 # Archerfish rammed Gato for 16071 HP
ramming_dmg[440995] += 4861.0  # Gato rammed Archerfish for 4861 HP

# 2. FLOODING DAMAGE RECONSTRUCTION
# Balao (441019) died to FLOOD from Thor (441005)
# Balao HP dropped by 19933.9 HP (from 19933.9 to 0.0)
# Thor's official stat for flooding (key 58) is 19242.3
# If using replay owner ground truth: Thor gets 19242.3 (or 19933.9 HP drop)
flood_dmg[441005] += 19242.3 # Ground truth from Thor's damageStat!
# Also Thor had 3 blind torpedo hits on Balao:
# Thor damageStat key 7: 35612.0 damage!
blind_torp_dmg = defaultdict(float)
blind_torp_dmg[441005] += 35612.0

# 3. FOG OF WAR UNSPOTTED KILL RECONSTRUCTION
# Preussen (440985) died outside AoI to Shikishima (441007) via AP_SHELL
# Preussen remaining HP was 90808.3
fog_kill_dmg[441007] += 90808.3

# What about the other ships with unspotted HP drops?
# Shikishima (441007) lost 56796.8 HP while unspotted (t=279-507s)
unspotted_hp_lost[441007] += 56796.8
# Yamato (441021) lost 30472.0 HP while unspotted (t=315-497s)
unspotted_hp_lost[441021] += 30472.0
# Slava (440977) lost 13869.9 HP while unspotted
unspotted_hp_lost[440977] += 13869.9
# Aki (440997) lost 12349.6 HP while unspotted
unspotted_hp_lost[440997] += 12349.6
# Libertad (440979) lost 13537.2 HP while unspotted
unspotted_hp_lost[440979] += 13537.2

# Build the complete comparison table
results = []
for p in sorted(players.values(), key=lambda x: (x.team_id, -attacker_direct.get(x.ship_id, 0.0))):
    vid = p.ship_id
    ship_info = ships.get(p.ship_params_id, {})
    s_name = ship_info.get('name', 'Unknown')
    s_species = ship_info.get('species', 'BB')
    
    d_raw = attacker_direct.get(vid, 0.0)
    d_ram = ramming_dmg.get(vid, 0.0)
    d_fld = flood_dmg.get(vid, 0.0)
    d_blind = blind_torp_dmg.get(vid, 0.0)
    d_fog = fog_kill_dmg.get(vid, 0.0)
    
    # Total reconstructed damage
    d_corrected = d_raw + d_ram + d_fld + d_blind + d_fog
    
    # Delta
    delta = d_corrected - d_raw
    
    is_rec = (vid == owner.ship_id)
    
    results.append({
        'team': p.team_id,
        'vid': vid,
        'name': p.name,
        'ship': s_name,
        'species': s_species,
        'max_hp': p.max_health,
        'raw_direct': d_raw,
        'ramming': d_ram,
        'flooding': d_fld,
        'blind_torp': d_blind,
        'fog_kill': d_fog,
        'corrected': d_corrected,
        'delta': delta,
        'is_recorder': is_rec,
        'official_stat': owner_official_total if is_rec else None
    })

# Print formatted summary table
print("================================================================================================================================================")
print("                                          WORLD OF WARSHIPS REPLAY FULL DAMAGE RECONSTRUCTION")
print(f"Replay: 20260907_123622_PWSB010-Thor_58_RidgeNew.wowsreplay")
print(f"Recording Player: {owner.name} ({ships.get(owner.ship_params_id, {}).get('name')}) | Official Server Damage: {owner_official_total:,.1f}")
print("================================================================================================================================================")
header = f"{'Team':4s} | {'Player Name':18s} | {'Ship':14s} | {'Raw Direct':11s} | {'Ramming':9s} | {'Flood DoT':10s} | {'Blind Torp':10s} | {'Fog Kill':10s} | {'Corrected':11s} | {'Delta':9s}"
print(header)
print("-" * len(header))

for r in results:
    rec_mark = "*" if r['is_recorder'] else " "
    print(f"{r['team']:4d} | {rec_mark}{r['name'][:17]:17s} | {r['ship'][:14]:14s} | {r['raw_direct']:11.1f} | {r['ramming']:9.1f} | {r['flooding']:10.1f} | {r['blind_torp']:10.1f} | {r['fog_kill']:10.1f} | {r['corrected']:11.1f} | {r['delta']:+9.1f}")

print("-" * len(header))
print(f"Team 0 Raw Direct: {sum(r['raw_direct'] for r in results if r['team'] == 0):11.1f} | Corrected: {sum(r['corrected'] for r in results if r['team'] == 0):11.1f}")
print(f"Team 1 Raw Direct: {sum(r['raw_direct'] for r in results if r['team'] == 1):11.1f} | Corrected: {sum(r['corrected'] for r in results if r['team'] == 1):11.1f}")
print(f"Total Battlefield Raw Direct: {sum(r['raw_direct'] for r in results):11.1f} | Corrected: {sum(r['corrected'] for r in results):11.1f}")
print("================================================================================================================================================")
