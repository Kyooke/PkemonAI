# simulate_turns.py
# ============================================
# ターンごとの自己施行AI
# 各ターンで他の行動を仮想的に試し、プレイング改善に反映
# ============================================

import os
import json
import random
from copy import deepcopy
from type_chart import TYPE_CHART
from build_team import safe_load_json, safe_save_json
from learn_playstyle import load_playstyle_memory

DATA_DIR = "data"
LOG_JSON = os.path.join(DATA_DIR, "battle_log.json")
PLAYSTYLE_JSON = os.path.join(DATA_DIR, "playstyle_memory.json")


# --------------------------------------------
# 効果倍率計算
# --------------------------------------------
def get_effectiveness(move_type, defender_types):
    e = 1.0
    for d in defender_types:
        e *= TYPE_CHART.get(move_type, {}).get(d, 1.0)
    return e


# --------------------------------------------
# 仮想ターンの結果をスコア化
# --------------------------------------------
def simulate_turn_result(action, my_pokemon, opp_types, home_data):
    """ターン単位での仮想結果スコアを返す"""
    my_data = home_data.get(my_pokemon, {})
    my_types = my_data.get("types", [])
    moves = my_data.get("moves", {})

    # 仮想行動の評価
    if action == "stay":
        return 0.5 + random.uniform(-0.1, 0.1)

    elif action == "use_u_turn":
        eff = get_effectiveness("むし", opp_types)
        return 0.6 + (eff - 1.0) * 0.2 + random.uniform(-0.1, 0.1)

    elif action == "switch":
        return 0.4 + random.uniform(-0.1, 0.1)

    elif action == "sacrifice":
        return 0.2 + random.uniform(-0.05, 0.05)

    elif action == "attack":
        # 攻撃技の仮想評価（最も有効なタイプで）
        best_eff = 1.0
        for mt in my_types:
            eff = get_effectiveness(mt, opp_types)
            best_eff = max(best_eff, eff)
        return 0.5 + (best_eff - 1.0) * 0.25 + random.uniform(-0.1, 0.1)

    else:
        return 0.5


# --------------------------------------------
# ターンごとの施行学習
# --------------------------------------------
def simulate_turn_learning():
    print("\n=== ターン施行AI（仮想プレイ分析） ===")

    log_path = LOG_JSON
    if not os.path.exists(log_path):
        print("⚠️ バトルログがありません。")
        return

    with open(log_path, "r", encoding="utf-8") as f:
        try:
            battle_logs = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ ログが壊れています。")
            return

    if not battle_logs:
        print("⚠️ ログが空です。")
        return

    home_data = safe_load_json(os.path.join(DATA_DIR, "home_data.json"))
    playstyle_memory = load_playstyle_memory()

    # 各バトル・ターンを走査
    for record in battle_logs[-3:]:  # 直近3試合だけ学習
        opp_team = record.get("opponent", [])
        for turn in record.get("turns", []):
            pokemon = turn.get("active")
            action = turn.get("action")
            if not pokemon or not action:
                continue

            # 仮想的に他の行動を試す
            possible_actions = ["stay", "switch", "use_u_turn", "sacrifice", "attack"]
            current_score = simulate_turn_result(action, pokemon, opp_team, home_data)

            for alt in possible_actions:
                if alt == action:
                    continue
                alt_score = simulate_turn_result(alt, pokemon, opp_team, home_data)

                key_real = f"{pokemon}:{action}"
                key_alt = f"{pokemon}:{alt}"

                # もし別行動の方が良ければペナルティを減らす
                if alt_score > current_score + 0.1:
                    playstyle_memory[key_alt] = playstyle_memory.get(key_alt, {"success": 0, "fail": 0})
                    playstyle_memory[key_alt]["success"] += 1
                    playstyle_memory[key_real] = playstyle_memory.get(key_real, {"success": 0, "fail": 0})
                    playstyle_memory[key_real]["fail"] += 1

    safe_save_json(PLAYSTYLE_JSON, playstyle_memory)
    print(f"💾 ターン単位プレイング施行を反映しました → {PLAYSTYLE_JSON}")
