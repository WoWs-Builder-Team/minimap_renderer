"""
World of Warships Replay Battle Report Infographic Generator
Generates a modern, ultra-high-definition (2.4K) post-battle scoreboard & stats summary image,
complete with full combat stats, weapon breakdown, medals, ribbons, and in-game match communications log.
"""

from __future__ import annotations

from io import BytesIO
import json
import math
import os
import struct
import sys
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from replay_parser import ReplayParser, CustomReader
from renderer.resman import ResourceManager

# Map names dictionary
MAP_NAMES: dict[str, str] = {
    "58_RidgeNew": "山脉",
    "37_Ridge": "山脉",
    "54_Faroe": "法罗群岛",
    "47_Sleeping_Giant": "沉睡的巨人",
    "42_Neighbors": "邻界群岛",
    "41_Conquest": "沙漠之泪",
    "40_Okinawa": "冲绳",
    "23_Shards": "碎钻群岛",
    "20_NE_two_brothers": "双子峡谷",
    "18_NE_ice_islands": "冰海追击",
    "15_NE_north": "北方之水",
    "35_NE_north_winter": "北方之水 (雪景)",
    "14_Atlantic": "大西洋",
    "55_Seychelles": "塞舌尔",
    "51_Greece": "希腊",
    "56_AngelWings": "天使之翼",
    "00_CO_ocean": "大洋",
    "17_NA_fault_line": "断层线",
    "10_NE_big_race": "大环礁",
    "46_Estuary": "河口",
    "52_Britain": "赫里福德海峡",
    "50_Gold_harbor": "黄金港",
    "45_Zigzag": "八爪群岛",
}

SCENARIO_NAMES: dict[str, str] = {
    "armsrace": "军备竞赛",
    "domination": "占领模式",
    "standard": "标准战斗",
    "epicenter": "震中模式",
    "airship": "飞艇向导",
}

GAME_TYPE_NAMES: dict[str, str] = {
    "RandomBattle": "随机战",
    "RankedBattle": "排位战",
    "ClanBattle": "军团战",
    "CooperativeBattle": "联合人机",
    "Operation": "行动模式",
}

SPECIES_SHORT: dict[str, str] = {
    "Battleship": "BB",
    "Cruiser": "CA",
    "Destroyer": "DD",
    "AirCarrier": "CV",
    "Submarine": "SS",
}

SPECIES_NAMES: dict[str, str] = {
    "Battleship": "战列舰",
    "Cruiser": "巡洋舰",
    "Destroyer": "驱逐舰",
    "AirCarrier": "航空母舰",
    "Submarine": "潜艇",
}

TIER_ROMAN = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "★"
}

ACHIEVEMENT_NAMES: dict[str, str] = {
    "AIRDEFENSEEXPERT": "防空专家",
    "INSTANT_KILL": "毁灭打击",
    "FIRST_BLOOD": "第一滴血",
    "MAIN_CALIBER": "大口径",
    "DREADNOUGHT": "坚不可摧",
    "KRAKEN": "海怪出没",
    "WITHERING": "凋零之火",
    "DOUBLE_KILL": "双重打击",
    "SOLO_WARRIOR": "孤胆英雄",
    "FIRESHOW": "纵火狂人",
    "UNSINKABLE": "灭火之王",
    "ARSONIST": "纵火犯",
    "CLEAR_SKY": "晴空万里",
}


def unpack_color(color_int: int) -> tuple[int, int, int]:
    """Unpacks ARGB color integer into (R, G, B)."""
    if color_int == 0 or color_int is None:
        return (235, 240, 245)
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return (r, g, b)


def format_datetime_zh(dt_str: str) -> str:
    """Formats date-time string like '07.09.2026 12:36:22' into '2026年09月07日 12:36:22'."""
    try:
        parts = dt_str.strip().split(" ", 1)
        if len(parts) == 2:
            d_parts = parts[0].split(".")
            time_part = parts[1]
            if len(d_parts) == 3:
                day, month, year = d_parts
                if len(year) == 4:
                    return f"{year}年{int(month):02d}月{int(day):02d}日 {time_part}"
                elif len(day) == 4:
                    return f"{day}年{int(month):02d}月{int(year):02d}日 {time_part}"
        elif len(parts) == 1:
            d_parts = parts[0].split(".")
            if len(d_parts) == 3:
                day, month, year = d_parts
                if len(year) == 4:
                    return f"{year}年{int(month):02d}月{int(day):02d}日"
        return dt_str
    except Exception:
        return dt_str


def extract_post_battle_results(replay_path: str) -> Optional[dict[str, Any]]:
    """Extracts official post-battle settlement results (Packet 0x22) from decrypted replay stream."""
    try:
        with open(replay_path, "rb") as f:
            reader = CustomReader(f)
            dec = reader.get_replay_data().decrypted_data
        io = BytesIO(dec)
        slen = len(dec)
        while io.tell() < slen:
            hdr = io.read(12)
            if len(hdr) < 12:
                break
            psize, ptype, _ = struct.unpack("IIf", hdr)
            if ptype == 0x22 and psize > 1024:
                jlen = struct.unpack("<I", io.read(4))[0]
                return json.loads(io.read(jlen).decode("utf-8", errors="replace"))
            io.seek(psize, 1)
    except Exception:
        pass
    return None


def parse_replay_report(replay_path: str) -> dict[str, Any]:
    """Parses replay and aggregates battle data with comprehensive damage reconstruction, AA & chat logs."""
    with open(replay_path, "rb") as fp:
        info = ReplayParser(fp).get_info()

    open_meta = info["open"]
    hidden = info["hidden"]
    rd = hidden["replay_data"]
    resman = ResourceManager(rd.game_version)
    ships = resman.load_json("ships.json")
    achievements_dict = resman.load_json("achievements.json")

    players = rd.player_info
    v_to_p = {p.ship_id: p for p in players.values()}
    owner = players[rd.owner_id]

    # Map & game info
    map_code = open_meta.get("mapDisplayName", "")
    map_title = MAP_NAMES.get(map_code, map_code.replace("_", " "))
    scenario_code = open_meta.get("scenario", "")
    scenario_title = SCENARIO_NAMES.get(scenario_code, scenario_code)
    game_type_code = open_meta.get("gameType", "")
    game_type_title = GAME_TYPE_NAMES.get(game_type_code, game_type_code)
    date_time = format_datetime_zh(open_meta.get("dateTime", ""))
    client_version = open_meta.get("clientVersionFromExe", rd.game_version)

    # 0. Check official post-battle settlement packet (Packet 0x22)
    post_battle = extract_post_battle_results(replay_path)
    has_post_battle = bool(post_battle and "playersPublicInfo" in post_battle)
    post_stats_by_dbid: dict[int, dict[str, Any]] = {}
    post_stats_by_name: dict[str, dict[str, Any]] = {}
    dbid_to_name: dict[int, str] = {}

    if has_post_battle:
        pub = post_battle["playersPublicInfo"]
        sample = list(pub.values())[0]
        d_idx = None
        for i, v in enumerate(sample):
            if any(isinstance(p_list[i], dict) and len(p_list[i]) > 0 for p_list in pub.values()):
                d_idx = i
                break
        if d_idx is None:
            for i, v in enumerate(sample):
                if isinstance(v, dict):
                    d_idx = i
                    break

        if d_idx is not None:
            for pid_str, p_data in pub.items():
                dbid_to_name[p_data[0]] = p_data[1]

            for pid_str, p_data in pub.items():
                p_stat = {
                    "account_dbid": p_data[0],
                    "name": p_data[1],
                    "base_xp": int(p_data[d_idx - 1]),  # Win XP (with 1.5x victory bonus matching in-game scoreboard)
                    "raw_xp": int(p_data[d_idx - 2]),   # Pure unmultiplied base XP
                    "damage": int(p_data[d_idx + 21]),
                    "killer_dbid": int(p_data[d_idx + 3]),
                    "death_reason": int(p_data[d_idx + 5]),
                    "spotting_damage": int(p_data[d_idx + 7]),
                    "potential_damage": int(p_data[d_idx + 11] + p_data[d_idx + 12] + p_data[d_idx + 13]),
                    "survival_time": float(p_data[22]),
                    "frags": int(p_data[32]),
                    "planes_killed": int(p_data[d_idx + 79]) if len(p_data) > d_idx + 79 else (int(p_data[280]) if len(p_data) > 280 else 0),
                }
                post_stats_by_dbid[p_stat["account_dbid"]] = p_stat
                post_stats_by_name[p_stat["name"]] = p_stat

    # 1. Base direct + visible fire damage from shots_damage_map
    shots_dmg = hidden.get("shots_damage_map", {})
    attacker_damage = {p.ship_id: 0.0 for p in players.values()}
    victim_direct = {p.ship_id: 0.0 for p in players.values()}
    for victim_id, attackers in shots_dmg.items():
        for att_id, dmg in attackers.items():
            attacker_damage[att_id] = attacker_damage.get(att_id, 0.0) + dmg
            victim_direct[victim_id] = victim_direct.get(victim_id, 0.0) + dmg

    # 2. HP drops & last active health tracking
    hp_last_active: dict[int, float] = {}
    hp_total_drops = {p.ship_id: 0.0 for p in players.values()}
    prev_hp: dict[int, float] = {}
    time_keys = sorted([k for k in rd.events.keys() if isinstance(k, int)])
    last_t = time_keys[-1] if time_keys else 0

    # Collect chat messages
    chat_items: list[dict[str, Any]] = []

    for t in time_keys:
        evt = rd.events[t]
        for vid, v in evt.evt_vehicle.items():
            if vid not in prev_hp:
                prev_hp[vid] = v.health
            else:
                diff = prev_hp[vid] - v.health
                if diff > 0:
                    hp_total_drops[vid] += diff
                prev_hp[vid] = v.health
            if v.health > 0:
                hp_last_active[vid] = v.health

        if evt.evt_chat:
            for m in evt.evt_chat:
                speaker = players.get(m.player_id)
                chat_items.append({
                    "time_sec": t,
                    "player_id": m.player_id,
                    "player_name": speaker.name if speaker else str(m.player_id),
                    "clan": speaker.clan_tag if speaker else "",
                    "clan_color": getattr(speaker, "clan_color", 0) if speaker else 0,
                    "team_id": speaker.team_id if speaker else -1,
                    "namespace": m.namespace,
                    "message": m.message,
                })

    # 3. Frags and death reasons
    death_info = hidden.get("death_info", {})
    frags = {p.ship_id: 0 for p in players.values()}
    killed_by: dict[int, tuple[int, str]] = {}
    for vid, d_data in death_info.items():
        k_id = d_data.get("killer_id", 0)
        killed_by[vid] = (k_id, d_data.get("name", ""))
        if k_id in frags:
            frags[k_id] += 1

    # 4. Compensate fire/flood tick damage for remaining unaccounted HP drops
    for vid, p in players.items():
        if vid in killed_by:
            killer_id, _ = killed_by[vid]
            accounted = victim_direct.get(vid, 0.0)
            lost = hp_total_drops.get(vid, 0.0)
            unaccounted = max(0.0, lost - accounted)
            if unaccounted > 50 and killer_id in attacker_damage and killer_id != vid:
                attacker_damage[killer_id] += unaccounted

    # 5. Owner specific stats
    damage_maps = hidden.get("damage_maps", {})
    owner_dmg_enemy = damage_maps.get("Enemy", {})
    owner_total_dmg = sum(v[1] for v in owner_dmg_enemy.values()) if owner_dmg_enemy else 0.0

    spot_map = damage_maps.get("Spot", {})
    owner_spot_dmg = sum(v[1] for v in spot_map.values()) if spot_map else 0.0

    agro_map = damage_maps.get("Agro", {})
    owner_agro_dmg = sum(v[1] for v in agro_map.values()) if agro_map else 0.0

    # Ribbons & main caliber details
    SOLO_MAP = {
        1: "torpedo", 3: "plane", 4: "crit", 5: "frag", 6: "burn", 7: "flood",
        8: "citadel", 9: "base_defense", 10: "base_capture", 11: "base_capture_assist",
        12: "suppressed", 13: "secondary_caliber", 18: "building_kill", 19: "detected",
        27: "splane", 31: "dbomb", 33: "drop", 54: "assist",
    }
    raw_ribbons = hidden.get("ribbons", {})
    owner_ribbons_raw = raw_ribbons.get(rd.owner_avatar_id) or raw_ribbons.get(owner.ship_id, {})
    processed_ribbons: dict[str, int] = {}
    main_caliber_details: dict[str, int] = {}
    if isinstance(owner_ribbons_raw, dict):
        for r_id, count in owner_ribbons_raw.items():
            name = None
            match r_id:
                case 0 | 14 | 15 | 16 | 17 | 28:
                    name = "main_caliber"
                    mc_type = {
                        14: "碎弹",
                        15: "过穿",
                        16: "跳弹",
                        17: "贯穿",
                        28: "未击穿"
                    }.get(r_id, "命中")
                    main_caliber_details[mc_type] = count
                case 24 | 25 | 26 | 30 | 34 | 35:
                    name = "rocket"
                case 2 | 20 | 21 | 22 | 23 | 29:
                    name = "bomb"
                case 39 | 40 | 41:
                    name = "acoustic_hit"
                case 43 | 44:
                    name = "dbomb"
                case 45:
                    name = "dbomb_mine"
                case _ as solo:
                    name = SOLO_MAP.get(solo, f"unknown_{solo}")
            if name:
                processed_ribbons.setdefault(name, 0)
                processed_ribbons[name] += count

    # Achievements
    owner_achievements: list[tuple[int, str]] = []
    raw_achs = hidden.get("achievements", {})
    owner_achs_raw = raw_achs.get(rd.owner_id) or raw_achs.get(rd.owner_avatar_id, {})
    if isinstance(owner_achs_raw, dict):
        for ach_id, count in owner_achs_raw.items():
            ach_name = achievements_dict.get(str(ach_id), {}).get("name", f"ACH_{ach_id}")
            owner_achievements.append((ach_id, ach_name))

    # Match outcome
    gr = rd.game_result
    is_victory = (gr.team_id == owner.team_id) if gr else False
    is_draw = (gr.team_id == -1) if gr else False
    final_score = {0: 0, 1: 0}
    for t in reversed(time_keys):
        if rd.events[t].evt_score:
            for tid, sc in rd.events[t].evt_score.items():
                final_score[tid] = sc.score
            break

    # Extract Division (pre-battle squad) info
    player_division_info: dict[int, dict[str, Any]] = {}
    team_div_counts: dict[int, int] = {0: 0, 1: 0}
    raw_players = hidden.get("players", {})

    if raw_players:
        team_squad_groups: dict[int, dict[int, list[Any]]] = {0: {}, 1: {}}
        for rp in raw_players.values():
            tid = rp.get("teamId", 0)
            pre_id = rp.get("preBattleIdOnStart", 0) or rp.get("prebattleId", 0)
            if pre_id > 0:
                team_squad_groups.setdefault(tid, {}).setdefault(pre_id, []).append(rp)

        for tid in (0, 1):
            valid_squads = [
                (s_id, mems) for s_id, mems in team_squad_groups.get(tid, {}).items()
                if len(mems) >= 2
            ]
            valid_squads.sort(key=lambda item: min(m.get("shipId", 0) for m in item[1]))
            team_div_counts[tid] = len(valid_squads)

            owner_raw_pre_id = 0
            for rp in raw_players.values():
                if rp.get("shipId") == owner.ship_id:
                    owner_raw_pre_id = rp.get("preBattleIdOnStart", 0) or rp.get("prebattleId", 0)
                    break

            for squad_num, (s_id, mems) in enumerate(valid_squads, start=1):
                mem_names = [m.get("name", "") for m in mems]
                is_owner_div = (s_id == owner_raw_pre_id and owner_raw_pre_id > 0)
                for rp in mems:
                    v_id = rp.get("shipId", 0)
                    player_division_info[v_id] = {
                        "division_num": squad_num,
                        "division_raw_id": s_id,
                        "is_owner_division": is_owner_div,
                        "is_leader": rp.get("isPreBattleOwner", False),
                        "division_members": mem_names,
                    }

    # Compile player list
    player_rows = []
    for p in players.values():
        vid = p.ship_id
        ship_info = ships.get(p.ship_params_id, {})
        s_name = ship_info.get("name", "Unknown")
        s_species = ship_info.get("species", "Battleship")
        s_level = ship_info.get("level", 10)

        d_out = attacker_damage.get(vid, 0.0)
        d_in = victim_direct.get(vid, 0.0)
        tot_hp_lost = hp_total_drops.get(vid, 0.0)
        k = frags.get(vid, 0)
        is_sunk = vid in killed_by
        killer_name = ""
        if is_sunk:
            killer_vid = killed_by[vid][0]
            if killer_vid in v_to_p:
                killer_name = v_to_p[killer_vid].name

        # Use official post-battle stats if available
        stat = post_stats_by_dbid.get(p.account_db_id) or post_stats_by_name.get(p.name)
        if stat:
            d_out = float(stat["damage"])
            k = stat["frags"]
            is_sunk = (stat["killer_dbid"] != 0)
            killer_name = dbid_to_name.get(stat["killer_dbid"], "")
            base_xp = stat["base_xp"]
            raw_xp = stat["raw_xp"]
            spot_dmg = stat["spotting_damage"]
            potential_dmg = stat["potential_damage"]
            survival_sec = stat["survival_time"]
            planes_killed = stat.get("planes_killed", 0)
        else:
            base_xp = 0
            raw_xp = 0
            spot_dmg = 0
            potential_dmg = 0
            survival_sec = float(last_t)
            planes_killed = processed_ribbons.get("plane", 0) if (vid == owner.ship_id) else 0

        div_info = player_division_info.get(vid, {
            "division_num": 0,
            "division_raw_id": 0,
            "is_owner_division": False,
            "is_leader": False,
            "division_members": [],
        })

        player_rows.append({
            "player_id": p.id,
            "ship_id": vid,
            "name": p.name,
            "clan": p.clan_tag,
            "clan_color": getattr(p, "clan_color", 0),
            "team_id": p.team_id,
            "is_owner": (vid == owner.ship_id),
            "ship_name": s_name,
            "species": s_species,
            "level": s_level,
            "frags": k,
            "planes_killed": planes_killed,
            "damage_dealt": d_out,
            "damage_taken": max(d_in, tot_hp_lost),
            "base_xp": base_xp,
            "raw_xp": raw_xp,
            "spotting_damage": spot_dmg,
            "potential_damage": potential_dmg,
            "survival_sec": survival_sec,
            "is_sunk": is_sunk,
            "killer_name": killer_name,
            "division_num": div_info["division_num"],
            "division_raw_id": div_info["division_raw_id"],
            "is_owner_division": div_info["is_owner_division"],
            "is_division_leader": div_info["is_leader"],
            "division_members": div_info["division_members"],
        })

    owner_div_info = player_division_info.get(owner.ship_id, {})
    owner_post = post_stats_by_dbid.get(owner.account_db_id) or post_stats_by_name.get(owner.name)

    return {
        "map_code": map_code,
        "map_title": map_title,
        "scenario_title": scenario_title,
        "game_type_title": game_type_title,
        "date_time": date_time,
        "client_version": client_version,
        "duration_sec": last_t,
        "is_victory": is_victory,
        "is_draw": is_draw,
        "final_score": final_score,
        "has_post_battle": has_post_battle,
        "team_division_counts": team_div_counts,
        "owner": {
            "name": owner.name,
            "clan": owner.clan_tag,
            "clan_color": getattr(owner, "clan_color", 0),
            "ship_name": ships.get(owner.ship_params_id, {}).get("name", "THOR"),
            "species": ships.get(owner.ship_params_id, {}).get("species", "Battleship"),
            "level": ships.get(owner.ship_params_id, {}).get("level", 10),
            "nation": ships.get(owner.ship_params_id, {}).get("nation", "Europe"),
            "team_id": owner.team_id,
            "total_dmg": float(owner_post["damage"]) if owner_post else owner_total_dmg,
            "base_xp": owner_post["base_xp"] if owner_post else 0,
            "raw_xp": owner_post["raw_xp"] if owner_post else 0,
            "spot_dmg": owner_post["spotting_damage"] if owner_post else owner_spot_dmg,
            "agro_dmg": owner_post["potential_damage"] if owner_post else owner_agro_dmg,
            "frags": owner_post["frags"] if owner_post else frags.get(owner.ship_id, 0),
            "planes_killed": processed_ribbons.get("plane", 0),
            "damage_breakdown": owner_dmg_enemy,
            "ribbons": processed_ribbons,
            "main_caliber_details": main_caliber_details,
            "achievements": owner_achievements,
            "is_sunk": (owner_post["killer_dbid"] != 0) if owner_post else (owner.ship_id in killed_by),
            "killer_name": dbid_to_name.get(owner_post["killer_dbid"], "") if owner_post else (v_to_p[killed_by[owner.ship_id][0]].name if owner.ship_id in killed_by and killed_by[owner.ship_id][0] in v_to_p else ""),
            "division_num": owner_div_info.get("division_num", 0),
            "division_members": owner_div_info.get("division_members", []),
            "is_division_leader": owner_div_info.get("is_leader", False),
        },
        "players": player_rows,
        "chat": chat_items,
    }


def draw_rounded_rect(draw: ImageDraw.Draw, xy, radius=10, fill=None, outline=None, width=1):
    """Draws a modern rounded rectangle."""
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def fit_text_ellipsis(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    """Safely sanitizes and truncates text with ellipsis if it exceeds max_width."""
    cleaned = text.replace("\r\n", " ").replace("\n", " ").strip()
    bbox = font.getbbox(cleaned)
    if bbox[2] - bbox[0] <= max_width:
        return cleaned

    ellipsis = "..."
    ell_w = font.getbbox(ellipsis)[2] - font.getbbox(ellipsis)[0]
    avail = max_width - ell_w
    if avail <= 0:
        return ellipsis

    low, high = 0, len(cleaned)
    best = 0
    while low <= high:
        mid = (low + high) // 2
        w = font.getbbox(cleaned[:mid])[2] - font.getbbox(cleaned[:mid])[0]
        if w <= avail:
            best = mid
            low = mid + 1
        else:
            high = mid - 1
    return cleaned[:best].rstrip() + ellipsis


def render_battle_report_card(data: dict[str, Any], output_path: str) -> str:
    """Renders the 2.4K Ultra-HD battle report graphic card and saves it to output_path."""
    W = 2400

    # Layout heights
    HEADER_Y = 28
    HEADER_H = 136

    HERO_Y = 180
    HERO_H = 320

    PANEL_Y = 518
    PANEL_H = 880

    # Compute chat section dimensions: render ALL in-game chat messages without capping
    chat_list = data.get("chat", [])
    num_chats = len(chat_list)
    chat_rows = max(1, math.ceil(num_chats / 2))
    bubble_h = 42
    bubble_gap = 8

    if num_chats == 0:
        chat_box_h = 140
    else:
        chat_box_h = max(140, 64 + chat_rows * (bubble_h + bubble_gap) + 16)

    CHAT_Y = PANEL_Y + PANEL_H + 20
    FOOTER_Y = CHAT_Y + chat_box_h + 18
    H = FOOTER_Y + 50

    img = Image.new("RGBA", (W, H), (12, 17, 24, 255))
    draw = ImageDraw.Draw(img)

    res_dir = os.path.join(os.path.dirname(__file__), "resources")
    font_path = os.path.join(res_dir, "warhelios_bold_zh.ttf")
    if not os.path.exists(font_path):
        font_path = os.path.join(res_dir, "warhelios_bold.ttf")

    def f(size: int):
        return ImageFont.truetype(font_path, size)

    # Subtle background tactical grid
    for y in range(0, H, 50):
        draw.line([(0, y), (W, y)], fill=(16, 23, 33, 255), width=1)
    for x in range(0, W, 50):
        draw.line([(x, 0), (x, H)], fill=(16, 23, 33, 255), width=1)

    # -------------------------------------------------------------
    # 1. TOP HEADER BAR (y: 28 .. 164)
    # -------------------------------------------------------------
    header_box = (35, HEADER_Y, W - 35, HEADER_Y + HEADER_H)
    draw_rounded_rect(draw, header_box, radius=14, fill=(18, 27, 39, 235), outline=(32, 48, 68, 255), width=1)

    # Left: Map & Game Mode
    map_text = f"{data['map_title']} · {data['map_code']}"
    draw.text((65, HEADER_Y + 22), map_text, fill=(255, 255, 255), font=f(30))
    mode_text = f"{data['scenario_title']} · {data['game_type_title']} (12 vs 12)   |   对局时间: {data['date_time']}"
    draw.text((65, HEADER_Y + 76), mode_text, fill=(145, 165, 185), font=f(18))

    # Center: VICTORY / DEFEAT Badge
    is_vic = data["is_victory"]
    is_draw = data["is_draw"]
    if is_draw:
        res_title = "DRAW · 平局"
        res_color = (241, 196, 15)
        res_bg = (50, 42, 15, 220)
    elif is_vic:
        res_title = "VICTORY · 战斗胜利"
        res_color = (46, 213, 115)
        res_bg = (18, 55, 34, 220)
    else:
        res_title = "DEFEAT · 战斗失败"
        res_color = (255, 71, 87)
        res_bg = (58, 22, 28, 220)

    res_badge_box = (W // 2 - 200, HEADER_Y + 18, W // 2 + 200, HEADER_Y + 78)
    draw_rounded_rect(draw, res_badge_box, radius=10, fill=res_bg, outline=res_color, width=2)
    t_bbox = f(30).getbbox(res_title)
    tw = t_bbox[2] - t_bbox[0]
    draw.text((W // 2 - tw // 2, HEADER_Y + 28), res_title, fill=res_color, font=f(30))

    dur_m = data["duration_sec"] // 60
    dur_s = data["duration_sec"] % 60
    dur_text = f"战斗用时 {dur_m:02d}:{dur_s:02d} · 积分争夺模式判定"
    sub_bbox = f(15).getbbox(dur_text)
    draw.text((W // 2 - (sub_bbox[2] - sub_bbox[0]) // 2, HEADER_Y + 92), dur_text, fill=(125, 142, 162), font=f(15))

    # Right: Scores
    s_ally = data["final_score"].get(data["owner"]["team_id"], 0)
    s_enemy = data["final_score"].get(1 - data["owner"]["team_id"], 0)
    draw.text((W - 400, HEADER_Y + 28), "比分", fill=(140, 158, 178), font=f(18))
    draw.text((W - 340, HEADER_Y + 20), f"{s_ally}", fill=(46, 213, 115), font=f(36))
    draw.text((W - 250, HEADER_Y + 22), ":", fill=(160, 170, 180), font=f(30))
    draw.text((W - 225, HEADER_Y + 20), f"{s_enemy}", fill=(255, 71, 87), font=f(36))
    draw.text((W - 400, HEADER_Y + 78), f"客户端版本: {data['client_version']}", fill=(105, 122, 142), font=f(15))

    # -------------------------------------------------------------
    # 2. OWNER SPOTLIGHT HERO CARD (y: 180 .. 500)
    # -------------------------------------------------------------
    card_box = (35, HERO_Y, W - 35, HERO_Y + HERO_H)
    draw_rounded_rect(draw, card_box, radius=14, fill=(20, 30, 44, 240), outline=(0, 206, 201, 160), width=1)

    ow = data["owner"]

    # Left Column: Identity (x: 65 .. 600)
    tier_str = TIER_ROMAN.get(ow["level"], str(ow["level"]))
    spec_str = SPECIES_NAMES.get(ow["species"], ow["species"])
    tag_ship = f"[{tier_str} {spec_str} · {ow['nation']}]"
    draw.text((65, HERO_Y + 25), tag_ship, fill=(0, 206, 201), font=f(17))
    draw.text((65, HERO_Y + 54), ow["ship_name"], fill=(255, 255, 255), font=f(44))

    px = 65
    if ow["clan"]:
        c_col = unpack_color(ow.get("clan_color", 0))
        c_tag = f"[{ow['clan']}] "
        draw.text((px, HERO_Y + 120), c_tag, fill=c_col, font=f(24))
        cw = f(24).getbbox(c_tag)[2] - f(24).getbbox(c_tag)[0]
        px += cw
    draw.text((px, HERO_Y + 120), ow["name"], fill=(240, 244, 248), font=f(24))

    if ow["is_sunk"]:
        st_text = f"战斗损毁 (击沉者: {ow['killer_name']})"
        st_color = (255, 107, 129)
    else:
        st_text = "整场存活 (Survive)"
        st_color = (46, 213, 115)
    draw.text((65, HERO_Y + 162), st_text, fill=st_color, font=f(17))

    # Owner Division Badge in Hero card
    if ow.get("division_num", 0) > 0:
        div_no = ow["division_num"]
        mates = [m for m in ow.get("division_members", []) if m != ow["name"]]
        mates_txt = f" · 搭档: {', '.join(mates)}" if mates else ""
        div_title = f"★ 组队出战 [分队 {div_no}]{mates_txt}"
        bw = f(14).getbbox(div_title)[2] - f(14).getbbox(div_title)[0]
        draw_rounded_rect(draw, (65, HERO_Y + 196, 65 + bw + 24, HERO_Y + 228), radius=6, fill=(48, 38, 14, 220), outline=(255, 195, 18, 220), width=1)
        draw.text((77, HERO_Y + 202), div_title, fill=(255, 215, 60), font=f(14))

    # Divider 1
    draw.line([(620, HERO_Y + 20), (620, HERO_Y + HERO_H - 20)], fill=(32, 48, 68, 255), width=1)

    # Middle Column: Performance (x: 645 .. 1560)
    draw.text((645, HERO_Y + 20), "造成对敌总伤害 (TOTAL DAMAGE)", fill=(140, 158, 178), font=f(16))
    dmg_num = f"{ow['total_dmg']:,.0f}"
    draw.text((645, HERO_Y + 45), dmg_num, fill=(0, 235, 255), font=f(56))

    # Breakdown tags
    bd_parts = []
    for w_id, (hits, dmg) in ow["damage_breakdown"].items():
        if w_id == 1:
            bd_parts.append(f"主炮 {dmg:,.0f}")
        elif w_id == 7:
            bd_parts.append(f"撞击 {dmg:,.0f}")
        elif w_id == 20 or w_id == 6:
            bd_parts.append(f"起火 {dmg:,.0f}")
        elif w_id == 58 or w_id == 2:
            bd_parts.append(f"副炮 {dmg:,.0f}")
        elif w_id == 4:
            bd_parts.append(f"空袭 {dmg:,.0f}")
    bd_str = "   ·   ".join(bd_parts) if bd_parts else "直接火力全额输出"
    draw.text((645, HERO_Y + 120), bd_str, fill=(160, 178, 198), font=f(15))

    # 4 stat boxes (w: 215, h: 96)
    stats_data = [
        ("击沉战舰", f"{ow['frags']}", "frags.png", (255, 71, 87)),
        ("击落战机", f"{ow['planes_killed']}", "caused_avia_damage.png", (255, 211, 42)),
        ("协助点亮", f"{ow['spot_dmg']:,.0f}", "assisted_damage.png", (0, 206, 201)),
        ("潜在承伤", f"{ow['agro_dmg']:,.0f}", "blocked_damage.png", (112, 161, 255)),
    ]

    for idx, (label, val, icon_name, color) in enumerate(stats_data):
        bx = 645 + idx * 228
        by = HERO_Y + 172
        draw_rounded_rect(draw, (bx, by, bx + 215, by + 105), radius=10, fill=(26, 38, 54, 220), outline=(42, 60, 84, 255), width=1)
        draw.text((bx + 16, by + 14), label, fill=(130, 148, 168), font=f(15))
        draw.text((bx + 16, by + 46), val, fill=color, font=f(30))

        icon_path = os.path.join(res_dir, "counter_icons", icon_name)
        if not os.path.exists(icon_path):
            icon_path = os.path.join(res_dir, "frag_icons", icon_name)
        if os.path.exists(icon_path):
            try:
                ic = Image.open(icon_path).convert("RGBA").resize((34, 34), Image.Resampling.LANCZOS)
                img.paste(ic, (bx + 165, by + 14), ic)
            except Exception:
                pass

    # Divider 2
    draw.line([(1580, HERO_Y + 20), (1580, HERO_Y + HERO_H - 20)], fill=(32, 48, 68, 255), width=1)

    # Right Column: Achievements & Ribbons (x: 1605 .. W-55)
    draw.text((1605, HERO_Y + 20), "当局勋章 & 战功勋带", fill=(140, 158, 178), font=f(16))

    # Medals
    ach_x = 1605
    for ach_id, ach_code in ow["achievements"]:
        ach_file = os.path.join(res_dir, "achievement_icons", f"icon_achievement_{ach_code}.png")
        if os.path.exists(ach_file):
            try:
                ach_img = Image.open(ach_file).convert("RGBA").resize((60, 60), Image.Resampling.LANCZOS)
                img.paste(ach_img, (ach_x, HERO_Y + 50), ach_img)
                ach_title = ACHIEVEMENT_NAMES.get(ach_code, ach_code[:8])
                draw.text((ach_x + 2, HERO_Y + 116), ach_title, fill=(255, 204, 0), font=f(14))
                ach_x += 92
            except Exception:
                pass

    # Ribbons (5 per row)
    ribbon_order = [
        "frag",
        "citadel",
        "main_caliber",
        "torpedo",
        "flood",
        "plane",
        "secondary_caliber",
        "crit",
        "dbomb",
        "detected",
    ]
    r_x = 1605
    r_y = HERO_Y + 155
    chip_w = 138
    chip_h = 44
    gap_x = 12
    gap_y = 10
    col_idx = 0
    row_idx = 0

    for r_key in ribbon_order:
        r_cnt = ow["ribbons"].get(r_key, 0)
        if r_cnt > 0:
            cx = r_x + col_idx * (chip_w + gap_x)
            cy = r_y + row_idx * (chip_h + gap_y)

            draw_rounded_rect(draw, (cx, cy, cx + chip_w, cy + chip_h), radius=8, fill=(26, 38, 54, 220), outline=(42, 60, 84, 255), width=1)

            r_file = os.path.join(res_dir, "ribbon_icons", f"ribbon_{r_key}.png")
            if os.path.exists(r_file):
                try:
                    r_img = Image.open(r_file).convert("RGBA").resize((60, 26), Image.Resampling.LANCZOS)
                    img.paste(r_img, (cx + 8, cy + 9), r_img)
                except Exception:
                    pass
            draw.text((cx + 78, cy + 10), f"×{r_cnt}", fill=(245, 245, 245), font=f(17))

            col_idx += 1
            if col_idx >= 5:
                col_idx = 0
                row_idx += 1

    # Main caliber detail
    if ow.get("main_caliber_details"):
        mc_parts = [f"{k} {v}" for k, v in ow["main_caliber_details"].items()]
        mc_text = "主炮明细: " + " · ".join(mc_parts)
        draw.text((r_x, HERO_Y + 270), mc_text, fill=(130, 148, 168), font=f(14))

    # -------------------------------------------------------------
    # 3. FULL TEAM SCOREBOARDS (y: PANEL_Y .. PANEL_Y + PANEL_H)
    # -------------------------------------------------------------
    HALF_W = (W - 70 - 25) // 2  # ~1150 px each

    ally_team_id = ow["team_id"]
    enemy_team_id = 1 - ally_team_id

    allies = [p for p in data["players"] if p["team_id"] == ally_team_id]
    enemies = [p for p in data["players"] if p["team_id"] == enemy_team_id]

    has_pb = data.get("has_post_battle", False)
    if has_pb:
        allies.sort(key=lambda p: (p.get("base_xp", 0), p["damage_dealt"]), reverse=True)
        enemies.sort(key=lambda p: (p.get("base_xp", 0), p["damage_dealt"]), reverse=True)
    else:
        allies.sort(key=lambda p: p["damage_dealt"], reverse=True)
        enemies.sort(key=lambda p: p["damage_dealt"], reverse=True)

    tot_ally_dmg = sum(p["damage_dealt"] for p in allies)
    tot_ally_k = sum(p["frags"] for p in allies)
    tot_enemy_dmg = sum(p["damage_dealt"] for p in enemies)
    tot_enemy_k = sum(p["frags"] for p in enemies)

    def render_team_panel(start_x: int, team_name: str, team_color: tuple, team_dmg: float, team_k: int, plist: list[dict], num_divs: int = 0):
        p_box = (start_x, PANEL_Y, start_x + HALF_W, PANEL_Y + PANEL_H)
        draw_rounded_rect(draw, p_box, radius=12, fill=(18, 26, 38, 240), outline=(32, 48, 68, 255), width=1)

        # Panel Header (h: 52)
        draw.rounded_rectangle((start_x, PANEL_Y, start_x + HALF_W, PANEL_Y + 52), radius=12, fill=(24, 36, 52, 255))
        draw.rounded_rectangle((start_x, PANEL_Y, start_x + 8, PANEL_Y + 52), radius=3, fill=team_color)

        draw.text((start_x + 25, PANEL_Y + 14), team_name, fill=(255, 255, 255), font=f(21))
        team_pk = sum(p.get("planes_killed", 0) for p in plist)
        div_str = f"     组队: {num_divs} 组" if num_divs > 0 else ""
        team_summary = f"全队击沉: {team_k}   击落: {team_pk}     全队总输出: {team_dmg:,.0f}{div_str}"
        sum_bbox = f(16).getbbox(team_summary)
        sum_w = sum_bbox[2] - sum_bbox[0]
        draw.text((start_x + HALF_W - 25 - sum_w, PANEL_Y + 16), team_summary, fill=team_color, font=f(16))

        # Column Subheaders
        col_y = PANEL_Y + 60
        if has_pb:
            draw.text((start_x + 25, col_y), "战舰型号", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 225, col_y), "玩家昵称", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 450, col_y), "击杀", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 496, col_y), "飞机", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 550, col_y), "造成伤害", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 645, col_y), "承受伤害", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 740, col_y), "基础经验", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 835, col_y), "原始裸经验", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 965, col_y), "战斗状态", fill=(110, 128, 148), font=f(15))
        else:
            draw.text((start_x + 25, col_y), "战舰型号", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 275, col_y), "玩家昵称", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 580, col_y), "击杀", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 695, col_y), "造成伤害", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 865, col_y), "承受伤害", fill=(110, 128, 148), font=f(15))
            draw.text((start_x + 1020, col_y), "战斗状态", fill=(110, 128, 148), font=f(15))

        draw.line([(start_x + 20, col_y + 26), (start_x + HALF_W - 20, col_y + 26)], fill=(28, 42, 60, 255), width=1)

        # 12 Rows
        row_y = col_y + 34
        row_h = 63

        for idx, p in enumerate(plist):
            ry = row_y + idx * row_h
            div_num = p.get("division_num", 0)
            is_own_div = p.get("is_owner_division", False)

            # Highlight owner or division mate
            if p["is_owner"]:
                draw_rounded_rect(draw, (start_x + 10, ry - 3, start_x + HALF_W - 10, ry + row_h - 7), radius=8, fill=(20, 48, 62, 235), outline=(0, 235, 255, 255), width=1)
            elif is_own_div:
                # Highlight owner's division mate (warm gold outline & soft amber tint)
                draw_rounded_rect(draw, (start_x + 10, ry - 3, start_x + HALF_W - 10, ry + row_h - 7), radius=8, fill=(35, 30, 16, 180), outline=(243, 156, 18, 160), width=1)
            elif idx % 2 == 1:
                draw_rounded_rect(draw, (start_x + 10, ry - 3, start_x + HALF_W - 10, ry + row_h - 7), radius=8, fill=(20, 29, 42, 160))

            # Vertical division strip on the left edge if in division
            if div_num > 0:
                if is_own_div:
                    strip_col = (255, 195, 18)
                elif p["team_id"] == ally_team_id:
                    strip_col = (46, 213, 115)
                else:
                    enemy_strip_cols = [(255, 71, 87), (218, 92, 235), (243, 156, 18)]
                    strip_col = enemy_strip_cols[(div_num - 1) % len(enemy_strip_cols)]
                draw.rounded_rectangle((start_x + 10, ry + 4, start_x + 15, ry + row_h - 14), radius=2, fill=strip_col)

            tier = TIER_ROMAN.get(p["level"], str(p["level"]))
            spec = SPECIES_SHORT.get(p["species"], p["species"][:2])
            ship_label = f"{tier} {p['ship_name']}"

            if p["is_sunk"]:
                name_color = (175, 185, 195)
                ship_color = (155, 168, 180)
            else:
                name_color = (255, 255, 255)
                ship_color = (235, 242, 250)

            if p["is_owner"]:
                name_color = (0, 235, 255)
            elif is_own_div:
                # Authentic WoWs golden yellow for division mates
                name_color = (255, 215, 60) if not p["is_sunk"] else (210, 180, 80)

            # Ship species badge
            draw.text((start_x + 25, ry + 10), f"[{spec}]", fill=team_color, font=f(14))
            draw.text((start_x + 65, ry + 8), ship_label[:14 if has_pb else 18], fill=ship_color, font=f(17))

            # Player name with authentic clan_color and division badge
            px_cur = start_x + (225 if has_pb else 275)

            # Render Division Badge if in division
            if div_num > 0:
                badge_w = 40
                badge_h = 22
                badge_box = (px_cur, ry + 7, px_cur + badge_w, ry + 7 + badge_h)
                if is_own_div:
                    b_fill = (65, 48, 12, 240)
                    b_out = (255, 195, 18, 255)
                    t_col = (255, 215, 50)
                elif p["team_id"] == ally_team_id:
                    b_fill = (15, 52, 35, 240)
                    b_out = (46, 213, 115, 255)
                    t_col = (46, 213, 115)
                else:
                    enemy_badges = [
                        ((60, 20, 26, 240), (255, 71, 87, 255), (255, 110, 120)),
                        ((52, 20, 58, 240), (218, 92, 235, 255), (230, 130, 240)),
                        ((58, 36, 12, 240), (243, 156, 18, 255), (250, 175, 45)),
                    ]
                    b_fill, b_out, t_col = enemy_badges[(div_num - 1) % len(enemy_badges)]

                draw_rounded_rect(draw, badge_box, radius=4, fill=b_fill, outline=b_out, width=1)
                b_text = f"队{div_num}"
                bw = f(13).getbbox(b_text)[2] - f(13).getbbox(b_text)[0]
                draw.text((px_cur + (badge_w - bw) // 2, ry + 9), b_text, fill=t_col, font=f(13))
                px_cur += badge_w + 8

            if p["clan"]:
                c_col = unpack_color(p.get("clan_color", 0))
                c_tag = f"[{p['clan']}] "
                draw.text((px_cur, ry + 8), c_tag, fill=c_col, font=f(17))
                c_w = f(17).getbbox(c_tag)[2] - f(17).getbbox(c_tag)[0]
                px_cur += c_w
            draw.text((px_cur, ry + 8), p["name"][:15 if has_pb else 20], fill=name_color, font=f(17))

            # Frags
            k = p["frags"]
            frag_x = start_x + (450 if has_pb else 580)
            if k > 0:
                k_box = (frag_x, ry + 7, frag_x + 30, ry + 35)
                k_bg = (255, 71, 87) if k >= 2 else (230, 126, 34)
                draw.rounded_rectangle(k_box, radius=5, fill=k_bg)
                kw = f(16).getbbox(f"{k}")[2] - f(16).getbbox(f"{k}")[0]
                draw.text((frag_x + 15 - kw // 2, ry + 9), f"{k}", fill=(255, 255, 255), font=f(16))
            else:
                draw.text((frag_x + 11, ry + 8), "-", fill=(75, 90, 110), font=f(16))

            if has_pb:
                # Planes Killed (AA defense)
                pk = p.get("planes_killed", 0)
                plane_x = start_x + 494
                if pk > 0:
                    pk_box = (plane_x, ry + 7, plane_x + 32, ry + 35)
                    pk_bg = (16, 52, 68, 240)
                    pk_out = (0, 206, 201, 240) if pk >= 15 else (0, 160, 180, 180)
                    pk_col = (0, 235, 255) if pk >= 15 else (180, 230, 245)
                    draw_rounded_rect(draw, pk_box, radius=5, fill=pk_bg, outline=pk_out, width=1)
                    pkw = f(15).getbbox(f"{pk}")[2] - f(15).getbbox(f"{pk}")[0]
                    draw.text((plane_x + 16 - pkw // 2, ry + 9), f"{pk}", fill=pk_col, font=f(15))
                else:
                    draw.text((plane_x + 12, ry + 8), "-", fill=(75, 90, 110), font=f(16))

                # Damage Dealt (right-aligned at start_x + 625)
                d_val = f"{p['damage_dealt']:,.0f}"
                d_col = (0, 235, 255) if p["damage_dealt"] > 100000 else ((245, 245, 245) if p["damage_dealt"] > 50000 else (165, 180, 195))
                dw = f(17).getbbox(d_val)[2] - f(17).getbbox(d_val)[0]
                draw.text((start_x + 625 - dw, ry + 8), d_val, fill=d_col, font=f(17))

                # Damage Taken (right-aligned at start_x + 720)
                t_val = f"{p['damage_taken']:,.0f}"
                tw = f(17).getbbox(t_val)[2] - f(17).getbbox(t_val)[0]
                draw.text((start_x + 720 - tw, ry + 8), t_val, fill=(150, 165, 180), font=f(17))

                # Base XP (Win XP, with 1.5x for victory, right-aligned at start_x + 815)
                bxp = p.get("base_xp", 0)
                xp_val = f"{bxp:,d}" if bxp > 0 else "-"
                xp_col = (255, 215, 60) if bxp >= 1500 else ((245, 245, 245) if bxp >= 1000 else (185, 200, 215))
                xpw = f(17).getbbox(xp_val)[2] - f(17).getbbox(xp_val)[0]
                draw.text((start_x + 815 - xpw, ry + 8), xp_val, fill=xp_col, font=f(17))

                # Raw Base XP (Pure unmultiplied base XP, right-aligned at start_x + 920)
                rxp = p.get("raw_xp", 0)
                rxp_val = f"{rxp:,d}" if rxp > 0 else "-"
                rxp_col = (210, 220, 230) if rxp >= 1000 else (145, 165, 185)
                rxpw = f(17).getbbox(rxp_val)[2] - f(17).getbbox(rxp_val)[0]
                draw.text((start_x + 920 - rxpw, ry + 8), rxp_val, fill=rxp_col, font=f(17))

                status_x = start_x + 965
            else:
                d_val = f"{p['damage_dealt']:,.0f}"
                d_col = (0, 235, 255) if p["damage_dealt"] > 100000 else ((245, 245, 245) if p["damage_dealt"] > 50000 else (165, 180, 195))
                dw = f(17).getbbox(d_val)[2] - f(17).getbbox(d_val)[0]
                draw.text((start_x + 785 - dw, ry + 8), d_val, fill=d_col, font=f(17))

                t_val = f"{p['damage_taken']:,.0f}"
                tw = f(17).getbbox(t_val)[2] - f(17).getbbox(t_val)[0]
                draw.text((start_x + 950 - tw, ry + 8), t_val, fill=(150, 165, 180), font=f(17))

                status_x = start_x + 1020

            # Status
            if p["is_sunk"]:
                k_txt = p["killer_name"][:11] if p["killer_name"] else ""
                draw.text((status_x, ry + 3), "沉没", fill=(255, 107, 129), font=f(14))
                if k_txt:
                    draw.text((status_x, ry + 25), f"by {k_txt}", fill=(130, 140, 150), font=f(12))
            else:
                draw.text((status_x, ry + 12), "● 存活", fill=(46, 213, 115), font=f(15))

    # Left: Allies
    ally_div_count = data.get("team_division_counts", {}).get(ally_team_id, 0)
    enemy_div_count = data.get("team_division_counts", {}).get(enemy_team_id, 0)

    ally_panel_title = "友方舰队 (Allies · 12 艘战舰)"
    render_team_panel(35, ally_panel_title, (46, 213, 115), tot_ally_dmg, tot_ally_k, allies, ally_div_count)

    # Right: Enemies
    enemy_panel_title = "敌方舰队 (Enemies · 12 艘战舰)"
    render_team_panel(35 + HALF_W + 25, enemy_panel_title, (255, 71, 87), tot_enemy_dmg, tot_enemy_k, enemies, enemy_div_count)

    # -------------------------------------------------------------
    # 4. COMMUNICATIONS & CHAT LOG SECTION (y: CHAT_Y .. CHAT_Y + chat_box_h)
    # -------------------------------------------------------------
    chat_box = (35, CHAT_Y, W - 35, CHAT_Y + chat_box_h)
    draw_rounded_rect(draw, chat_box, radius=12, fill=(18, 26, 38, 240), outline=(32, 48, 68, 255), width=1)

    # Header Bar
    draw.rounded_rectangle((35, CHAT_Y, W - 35, CHAT_Y + 50), radius=12, fill=(24, 36, 52, 255))
    draw.rounded_rectangle((35, CHAT_Y, 43, CHAT_Y + 50), radius=3, fill=(0, 206, 201))

    chat_title = f"战局通讯与全场互动记录 (Battle Communications Log · 共 {num_chats} 条发言)"
    draw.text((55, CHAT_Y + 12), chat_title, fill=(255, 255, 255), font=f(19))

    # Legend with authentic channel colors
    leg_x = W - 780
    draw.rounded_rectangle((leg_x, CHAT_Y + 13, leg_x + 50, CHAT_Y + 35), radius=4, fill=(40, 50, 65))
    draw.text((leg_x + 10, CHAT_Y + 14), "全体", fill=(240, 240, 240), font=f(13))
    draw.text((leg_x + 58, CHAT_Y + 14), "白字公共全频", fill=(200, 205, 210), font=f(13))

    leg_x += 185
    draw.rounded_rectangle((leg_x, CHAT_Y + 13, leg_x + 50, CHAT_Y + 35), radius=4, fill=(18, 55, 34))
    draw.text((leg_x + 10, CHAT_Y + 14), "团队", fill=(46, 213, 115), font=f(13))
    draw.text((leg_x + 58, CHAT_Y + 14), "绿字己方队友", fill=(46, 213, 115), font=f(13))

    leg_x += 185
    draw.rounded_rectangle((leg_x, CHAT_Y + 13, leg_x + 50, CHAT_Y + 35), radius=4, fill=(55, 42, 15))
    draw.text((leg_x + 10, CHAT_Y + 14), "分队", fill=(255, 204, 0), font=f(13))
    draw.text((leg_x + 58, CHAT_Y + 14), "黄字组队队友", fill=(255, 204, 0), font=f(13))

    # Chat Bubbles
    player_by_name = {p["name"]: p for p in data["players"]}
    if not chat_list:
        draw.text((W // 2 - 140, CHAT_Y + 70), "本场对局未记录到局内文字通讯消息", fill=(100, 120, 140), font=f(16))
    else:
        inner_pad = 20
        col_gap = 24
        col_w = (W - 70 - 2 * inner_pad - col_gap) // 2  # ~1133 px
        col_left_x = 35 + inner_pad
        col_right_x = col_left_x + col_w + col_gap

        half_count = math.ceil(num_chats / 2)
        for idx, item in enumerate(chat_list):
            is_left_col = (idx < half_count)
            row_in_col = idx if is_left_col else (idx - half_count)
            start_cx = col_left_x if is_left_col else col_right_x
            bubble_end_x = start_cx + col_w
            item_y = CHAT_Y + 62 + row_in_col * (bubble_h + bubble_gap)

            is_ally = (item["team_id"] == ally_team_id)
            ns = item["namespace"]
            is_div = ns in ("battle_division", "battle_prebattle")
            is_all = (ns == "battle_common")

            # Left accent stripe: division gold, ally green, enemy red
            if is_div:
                accent_col = (255, 204, 0)
            elif is_ally:
                accent_col = (46, 213, 115)
            else:
                accent_col = (255, 71, 87)

            # Bubble background
            draw_rounded_rect(draw, (start_cx, item_y, bubble_end_x, item_y + bubble_h), radius=6, fill=(24, 34, 48, 220), outline=(36, 52, 72, 255), width=1)
            # Left side stripe
            draw.rounded_rectangle((start_cx, item_y, start_cx + 5, item_y + bubble_h), radius=2, fill=accent_col)

            # Timestamp
            tm = item["time_sec"] // 60
            ts = item["time_sec"] % 60
            time_str = f"[{tm:02d}:{ts:02d}]"
            draw.text((start_cx + 14, item_y + 11), time_str, fill=(0, 206, 201), font=f(14))

            # Channel tag badge & message text color
            if is_div:
                tag_label = "分队"
                tag_bg = (55, 42, 15)
                tag_col = (255, 204, 0)
                name_col = (255, 204, 0)
                msg_col = (255, 215, 60)    # 金黄分队文字
            elif is_all:
                tag_label = "全体"
                if is_ally:
                    tag_bg = (18, 48, 35)
                    tag_col = (80, 220, 145)
                    name_col = (46, 213, 115)
                    msg_col = (115, 235, 160)   # 友方绿字
                else:
                    tag_bg = (50, 22, 28)
                    tag_col = (255, 110, 120)
                    name_col = (255, 120, 130)
                    msg_col = (255, 140, 150)   # 敌方红字
            else:  # battle_team
                tag_label = "团队"
                tag_bg = (18, 55, 34)
                tag_col = (46, 213, 115)
                name_col = (46, 213, 115)
                msg_col = (115, 235, 160)   # 友方绿字

            draw.rounded_rectangle((start_cx + 80, item_y + 9, start_cx + 124, item_y + 31), radius=4, fill=tag_bg)
            draw.text((start_cx + 87, item_y + 10), tag_label, fill=tag_col, font=f(12))

            # Sender Name with Division, Clan and Player Name
            sx = start_cx + 136
            speaker_p = player_by_name.get(item["player_name"])
            if speaker_p and speaker_p.get("division_num", 0) > 0:
                s_div = speaker_p["division_num"]
                s_div_tag = f"[队{s_div}] "
                s_div_col = (255, 215, 60) if speaker_p.get("is_owner_division") else ((46, 213, 115) if is_ally else (255, 110, 120))
                draw.text((sx, item_y + 10), s_div_tag, fill=s_div_col, font=f(14))
                sx += f(14).getbbox(s_div_tag)[2] - f(14).getbbox(s_div_tag)[0]

            if item["clan"]:
                c_col = unpack_color(item.get("clan_color", 0))
                c_str = f"[{item['clan']}] "
                draw.text((sx, item_y + 10), c_str, fill=c_col, font=f(15))
                sx += f(15).getbbox(c_str)[2] - f(15).getbbox(c_str)[0]

            p_name_str = f"{item['player_name']}: "
            draw.text((sx, item_y + 10), p_name_str, fill=name_col, font=f(15))
            sx += f(15).getbbox(p_name_str)[2] - f(15).getbbox(p_name_str)[0]

            # Message content with safe boundary clamping & ellipsis
            max_msg_w = max(50, bubble_end_x - sx - 16)
            safe_msg = fit_text_ellipsis(item["message"], f(16), max_msg_w)
            draw.text((sx, item_y + 10), safe_msg, fill=msg_col, font=f(16))

    # -------------------------------------------------------------
    # 5. BOTTOM FOOTER BAR (y: FOOTER_Y .. FOOTER_Y + 40)
    # -------------------------------------------------------------
    draw.text((45, FOOTER_Y + 6), "Minimap Renderer · 战舰世界战局分析与小地图视频渲染引擎", fill=(95, 115, 138), font=f(15))
    draw.text((W - 480, FOOTER_Y + 6), "数据源自 BigWorld Replay 原始数据包流解析", fill=(95, 115, 138), font=f(15))

    # Ensure parent dir exists
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # Save to disk
    img.save(output_path, "PNG")
    print(f"Ultra-HD Battle report successfully saved to: {output_path} ({W}x{H})")
    return output_path


def generate_battle_report(replay_path: str, output_path: Optional[str] = None) -> str:
    """Convenience helper: parses replay and renders battle report infographic card."""
    if output_path is None:
        output_path = os.path.splitext(replay_path)[0] + "-report.png"
    data = parse_replay_report(replay_path)
    return render_battle_report_card(data, output_path)
