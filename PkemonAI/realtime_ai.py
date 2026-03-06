# -*- coding: utf-8 -*-
# full_battle_ai.py
# ==========================================================
# 相手6体を見て3体選出＋交代＋技選択AI統合フルバトル
# ==========================================================

import os
import json
import random
from copy import deepcopy
from type_chart import TYPE_CHART
from identify_opponent import resolve_opponent_name
from input_home_data import safe_load_json, safe_save_json
from select_team import select_best_team_for_match

# ===== Utility =====
def get_effectiveness(move_type, defender_types):
    e = 1.0
    for d in defender_types:
        e *= TYPE_CHART.get(move_type, {}).get(d, 1.0)
    return e

# ===== 交代判断AI =====
def decide_switch_smart(my_active_name, my_hp, opponent_types, team_names, home_data,
                        field_hazards=None, opponent_info=None):
    if field_hazards is None:
        field_hazards = {"ステルスロック": True, "どくびし": True}
    if opponent_info is None:
        opponent_info = {"ability": "", "item": ""}

    CONTACT_DAMAGE_ABILITIES = {"さめはだ", "てつのトゲ"}
    CONTACT_DAMAGE_ITEMS = {"ゴツゴツメット"}
    HAZARD_TRIGGER_ABILITIES = {"どくげしょう"}

    def eff_score(att_types, def_types):
        total = 1.0
        for a in att_types:
            for d in def_types:
                total *= TYPE_CHART.get(a, {}).get(d, 1.0)
        return total

    def stealth_rock_damage(types):
        rock_eff = 1.0
        for t in types:
            rock_eff *= TYPE_CHART.get("いわ", {}).get(t, 1.0)
        return 12.5 * rock_eff

    def toxic_spikes_active(types):
        if any(t in types for t in ["どく", "じめん", "ひこう"]):
            return 0
        return 10

    def ability_bonus(ability, opp_types):
        if ability in ["さいせいりょく"]:
            return +20
        if ability in ["ちょすい"] and "みず" in opp_types:
            return +15
        if ability in ["もらいび"] and "ほのお" in opp_types:
            return +15
        if ability in ["ぼうおん"]:
            return +10
        if ability in CONTACT_DAMAGE_ABILITIES:
            return +6
        return 0

    def contact_reflect_risk(opp_ability, opp_item, my_is_physical):
        if not my_is_physical:
            return 0
        dmg = 0
        if opp_ability in CONTACT_DAMAGE_ABILITIES:
            dmg += 12.5
        if opp_item in CONTACT_DAMAGE_ITEMS:
            dmg += 16.6
        return dmg

    def toxic_debris_trigger(opp_ability, my_is_physical):
        if opp_ability in ["どくげしょう"] and my_is_physical:
            return 10
        return 0

    my_info = home_data.get(my_active_name, {})
    my_types = my_info.get("types", [])
    moves = list(my_info.get("moves", {}).keys()) if isinstance(my_info.get("moves", {}), dict) else []

    offense = eff_score(my_types, opponent_types)
    defense = eff_score(opponent_types, my_types)
    damage_expect = defense * (1 + (100 - my_hp)/100)

    if damage_expect >= 1.5:
        situation = "非常に不利"
    elif damage_expect >= 1.0:
        situation = "やや不利"
    elif damage_expect >= 0.7:
        situation = "中立"
    else:
        situation = "有利"

    teammates = [t for t in team_names if t != my_active_name]
    switch_candidates = []
    for mate in teammates:
        info = home_data.get(mate, {})
        tts = info.get("types", [])
        ab = info.get("ability", "")
        atk_eff = eff_score(tts, opponent_types)
        def_eff = eff_score(opponent_types, tts)

        hazard_penalty = 0
        if field_hazards.get("ステルスロック"):
            hazard_penalty += stealth_rock_damage(tts)
        if field_hazards.get("どくびし"):
            hazard_penalty += toxic_spikes_active(tts)

        ability_mod = ability_bonus(ab, opponent_types)
        contact_penalty = contact_reflect_risk(opponent_info.get("ability",""),
                                              opponent_info.get("item",""), True)
        debris_risk = toxic_debris_trigger(opponent_info.get("ability",""), True)
        debris_bonus = 15 if ab in HAZARD_TRIGGER_ABILITIES else 0

        score = (atk_eff / (def_eff + 0.1)) * 100
        score -= (hazard_penalty + contact_penalty + debris_risk) * 0.8
        score += ability_mod + debris_bonus
        switch_candidates.append((mate, round(score,2)))

    switch_candidates.sort(key=lambda x: x[1], reverse=True)
    best_switch = switch_candidates[0] if switch_candidates else None

    has_pivot_move = any(x in moves for x in ["とんぼがえり","ボルトチェンジ","クイックターン"])
    low_hp = my_hp < 30
    can_switch = best_switch and best_switch[1] > 100

    if situation == "有利":
        return ("stay", None, "有利対面: 続行")
    if has_pivot_move and situation != "有利":
        return ("use_u_turn", None, "交代技で安全撤退")
    if can_switch and situation in ["非常に不利","やや不利"] and not low_hp:
        return ("switch", best_switch[0], f"不利対面 → {best_switch[0]}に交代 (スコア={best_switch[1]})")
    if situation == "非常に不利" and low_hp:
        return ("sacrifice", None, "犠牲判断: 勝率優先")
    return ("stay", None, "中立判断: 続行")


# ===== 技選択AI =====
def choose_best_move_enhanced(pokemon_name, my_hp_pct, opponent_types, home_data, opponent_info=None):
    if opponent_info is None:
        opponent_info = {"ability":"","item":""}
    info = home_data.get(pokemon_name,{})
    moves_dict = info.get("moves",{}) if isinstance(info.get("moves",{}),dict) else {}
    if not moves_dict:
        return "わるだくみ"

    def estimate_move_score(move_name):
        move_meta = moves_dict.get(move_name,{})
        mtype = move_meta.get("type","ノーマル")
        power = move_meta.get("power",60)
        acc = move_meta.get("accuracy",100)
        makes_contact = move_meta.get("makes_contact",False)
        stab = 1.5 if mtype in info.get("types",[]) else 1.0
        eff = get_effectiveness(mtype, opponent_types)
        dmg = power*eff*stab*(acc/100)

        if opponent_info.get("ability")=="ちょすい" and mtype=="みず":
            return -999
        if opponent_info.get("ability")=="もらいび" and mtype=="ほのお":
            return -999

        contact_penalty = 0
        if makes_contact:
            if opponent_info.get("ability") in ["さめはだ","てつのトゲ"]:
                contact_penalty += 10
            if opponent_info.get("item") in ["ゴツゴツメット"]:
                contact_penalty += 15
        return dmg - contact_penalty

    scored = [(m, estimate_move_score(m)) for m in moves_dict.keys()]
    scored.sort(key=lambda x:x[1],reverse=True)
    return scored[0][0]


# ===== フルバトルAI =====
class FullBattleAI:
    def __init__(self):
        self.home_data = safe_load_json("data/home_data.json") or {}
        self.team_data = safe_load_json("data/team.json") or []
        if isinstance(self.team_data[0], str):
            self.team_data = [{"name": n} for n in self.team_data]
        self.names = [t["name"] for t in self.team_data]

    def simulate_battle(self, opponent_team_texts):
        print("=== フルバトルAI（相手6体→3体選出＋交代＋技選択） ===")
        opponent_team = [resolve_opponent_name(n) for n in opponent_team_texts]

        # ✅ AIで3体選出
        self.names = select_best_team_for_match(opponent_team)
        print(f"🔸 AI選出: {self.names}")

        my_active = self.names[0]
        my_hp_dict = {n:100 for n in self.names}
        opp_hp_dict = {n:100 for n in opponent_team}

        turn = 1
        max_turns = 20
        while turn <= max_turns and any(my_hp_dict.values()) and any(opp_hp_dict.values()):
            print(f"\n=== Turn {turn} ===")
            for my_poke in self.names:
                if my_hp_dict[my_poke]<=0:
                    continue
                opp_alive = [o for o in opponent_team if opp_hp_dict[o]>0]
                if not opp_alive:
                    break
                opp_active = opp_alive[0]
                opp_data = self.home_data.get(opp_active, {"types":["ノーマル"],"ability":"","item":""})
                opp_types = opp_data.get("types",["ノーマル"])
                opponent_info = {"ability":opp_data.get("ability",""),"item":opp_data.get("item","")}

                dec,target,reason = decide_switch_smart(my_poke,my_hp_dict[my_poke],opp_types,
                                                        self.names,self.home_data,
                                                        field_hazards={"ステルスロック":True,"どくびし":True},
                                                        opponent_info=opponent_info)
                print(f"{my_poke} の判断: {dec} ({reason})")
                if dec=="switch" and target:
                    print(f"→ {my_poke} → {target} に交代")
                    my_active = target
                elif dec=="use_u_turn":
                    print(f"→ {my_poke} 使用: とんぼがえりで交代")
                    my_active = self.names[1]
                elif dec=="sacrifice":
                    print(f"→ {my_poke} は犠牲に！")
                    my_hp_dict[my_poke]=0
                else:
                    move = choose_best_move_enhanced(my_poke,my_hp_dict[my_poke],opp_types,self.home_data,opponent_info)
                    dmg=random.randint(15,35)
                    opp_hp_dict[opp_active] = max(0,opp_hp_dict[opp_active]-dmg)
                    print(f"→ {my_poke} の {move}! {opp_active} HP {opp_hp_dict[opp_active]}")

            # 相手のターン（簡易攻撃）
            for opp_poke in opponent_team:
                if opp_hp_dict[opp_poke]<=0:
                    continue
                my_alive = [m for m in self.names if my_hp_dict[m]>0]
                if not my_alive:
                    break
                my_active = my_alive[0]
                dmg=random.randint(10,25)
                my_hp_dict[my_active]=max(0,my_hp_dict[my_active]-dmg)
                print(f"→ {opp_poke} の攻撃! {my_active} HP {my_hp_dict[my_active]}")

            turn+=1

        my_alive = any(v>0 for v in my_hp_dict.values())
        opp_alive = any(v>0 for v in opp_hp_dict.values())
        if my_alive and not opp_alive:
            result="win"
        elif not my_alive and opp_alive:
            result="lose"
        else:
            result="draw"
        print(f"\n🎮 バトル結果: {result.upper()}")


# ===== 実行部 =====
if __name__=="__main__":
    ai = FullBattleAI()
    opponent_texts = ["りゅうくん","つつみちゃん","バレル先生","サンダーさん","ミミッキュ","ドドゲザン"]
    ai.simulate_battle(opponent_texts)