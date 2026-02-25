# realtime_ai.py
# ============================================
# 改良版バトルAI（ニックネーム対応・犠牲判断＋相手記録＋PokéAPI連携）
# ============================================

import os
import json
import random
from datetime import datetime
from copy import deepcopy
from collections import defaultdict

from type_chart import TYPE_CHART
from identify_opponent import resolve_opponent_name
from input_home_data import safe_load_json, safe_save_json


# ===== Utility =====
def get_effectiveness(move_type, defender_types):
    e = 1.0
    for d in defender_types:
        e *= TYPE_CHART.get(move_type, {}).get(d, 1.0)
    return e


# ===== 交代判断AI =====
def decide_switch_smart(
    my_active_name, my_hp, opponent_types, team_names, home_data, last_move, must_preserve=False
):
    """
    改良版交代判断:
    - 有利対面: 交代しない
    - 不利対面: 交代候補がいれば交代
    - 交代技（とんぼがえり/ボルトチェンジ等）があるならそちらを優先
    - 勝ち筋上、切った方が良い場合はあえて残らず倒れる
    """
    my_info = home_data.get(my_active_name, {})
    my_types = my_info.get("types", [])
    role = my_info.get("role", "")
    moves = list(my_info.get("moves", {}).keys()) if isinstance(my_info.get("moves", {}), dict) else []

    def eff_vs(typesA, typesB):
        m = 1.0
        for a in typesA:
            for b in typesB:
                m *= TYPE_CHART.get(a, {}).get(b, 1.0)
        return m

    my_offense = eff_vs(my_types, opponent_types)
    my_defense = eff_vs(opponent_types, my_types)
    net_ratio = my_offense / (my_defense + 0.01)

    is_disadv = net_ratio < 0.8
    has_u_turn = any(x in moves for x in ["とんぼがえり", "ボルトチェンジ", "クイックターン"])
    low_hp = my_hp < 25

    teammates = [t for t in team_names if t != my_active_name]
    viable_switch = []
    for mate in teammates:
        info = home_data.get(mate, {})
        tts = info.get("types", [])
        resists = sum(1 for ot in opponent_types if get_effectiveness(ot, tts) < 1.0)
        viable_switch.append((mate, resists))
    best_switch = max(viable_switch, key=lambda x: x[1]) if viable_switch else None
    can_switch = best_switch and best_switch[1] > 0

    if not is_disadv:
        return ("stay", None, "有利対面のため居座り")
    if has_u_turn:
        return ("use_u_turn", None, "交代技で安全に撤退")
    if is_disadv and can_switch and not low_hp:
        return ("switch", best_switch[0], "不利対面、交代選択")
    if is_disadv and low_hp:
        return ("sacrifice", None, "勝率重視で犠牲出し")
    return ("stay", None, "中立判断")


# ===== 技選択AI =====
def choose_best_move(pokemon, opponent_types, home_data):
    info = home_data.get(pokemon, {})
    moves = list(info.get("moves", {}).keys()) if isinstance(info.get("moves", {}), dict) else []
    if not moves:
        return "わるだくみ"

    scored = []
    types = info.get("types", [])
    for m in moves:
        move_type = home_data.get(m, {}).get("type") or "ノーマル"
        eff = get_effectiveness(move_type, opponent_types)
        power = 80 if eff >= 1 else 60
        stab = 1.5 if move_type in types else 1.0
        scored.append((m, power * eff * stab))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]


# ===== 戦闘シミュレーター =====
class BattleAI:
    def __init__(self):
        self.team = safe_load_json("data/team.json") or []
        self.home_data = safe_load_json("data/home_data.json") or {}
        if isinstance(self.team[0], str):
            self.team = [{"name": n} for n in self.team]
        for t in self.team:
            n = t["name"]
            if n not in self.home_data:
                self.home_data[n] = {"types": ["ノーマル"], "moves": {"わるだくみ": 10}}
        self.names = [t["name"] for t in self.team]

    def simulate_battle(self, opponent_team_texts):
        print("=== 改良版バトルAI（ニックネーム対応） ===")

        # OCRで取得された相手名から正式名に変換
        opponent_team = [resolve_opponent_name(name) for name in opponent_team_texts]

        my_active = self.names[0]
        opp_active = opponent_team[0]
        opp_data = self.home_data.get(opp_active, {"types": ["ノーマル"]})
        opp_types = opp_data.get("types", ["ノーマル"])

        my_hp = 100.0
        opp_hp = 100.0
        turn = 1
        logs = []

        while turn <= 10 and my_hp > 0 and opp_hp > 0:
            dec, target, reason = decide_switch_smart(my_active, my_hp, opp_types, self.names, self.home_data, last_move=None)
            print(f"\n[Turn{turn}] {my_active} の判断: {dec} ({reason})")

            if dec == "use_u_turn":
                move = "とんぼがえり" if "とんぼがえり" in self.home_data.get(my_active, {}).get("moves", {}) else "ボルトチェンジ"
                dmg = random.randint(20, 35)
                opp_hp = max(0, opp_hp - dmg)
                target = self.names[1]
                my_active = target
                print(f"→ {move}！ {target}に交代！ 残HP {my_hp:.0f}")
            elif dec == "switch":
                print(f"→ {target}に交代！")
                my_active = target
                my_hp = max(0, my_hp - random.randint(5, 10))
            elif dec == "sacrifice":
                print(f"→ {my_active}は切る判断。攻撃を受けて倒れる。")
                my_hp = 0
                break
            else:
                move = choose_best_move(my_active, opp_types, self.home_data)
                dmg = random.randint(15, 30)
                opp_hp = max(0, opp_hp - dmg)
                print(f"→ {my_active}の{move}! 相手HP {opp_hp:.0f}")
                my_hp = max(0, my_hp - random.randint(10, 25))

            logs.append({
                "turn": turn,
                "action": dec,
                "active": my_active,
                "hp_after": my_hp,
                "opp_hp_after": opp_hp,
            })
            turn += 1

        result = "win" if opp_hp <= 0 else "lose" if my_hp <= 0 else "draw"
        print(f"\n🎮 結果: {result.upper()}")

        battle_record = {
            "opponent": opponent_team,
            "result": result,
            "turns": logs,
            "timestamp": datetime.now().isoformat()
        }

        log_path = "data/battle_log.json"
        old = safe_load_json(log_path) or []
        old.append(battle_record)
        safe_save_json(log_path, old)
        print(f"💾 ログ保存完了: {log_path}")


# ===== 実行部 =====
if __name__ == "__main__":
    ai = BattleAI()
    # 例：OCRで取得した相手の名前（ニックネーム含む）
    opponent_texts = ["りゅうくん", "つつみちゃん", "バレル先生"]
    ai.simulate_battle(opponent_texts)