# select_team.py
# ============================================
# 対戦相手に合わせて最適な3体を自動選出するAI
# ============================================

import os
import json
from itertools import combinations
from type_chart import TYPE_CHART


DATA_DIR = "data"
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")
TEAM_JSON = os.path.join(DATA_DIR, "team.json")
SELECT_JSON = os.path.join(DATA_DIR, "selected_team.json")


# --------------------------------------------
# JSON安全読み書き
# --------------------------------------------
def safe_load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ JSONエラー: {path}")
            return {}


def safe_save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --------------------------------------------
# タイプ相性スコア（有利度計算）
# --------------------------------------------
def type_advantage(attacker_types, defender_types):
    score = 1.0
    for atk in attacker_types:
        for d in defender_types:
            score *= TYPE_CHART.get(atk, {}).get(d, 1.0)
    return score


# --------------------------------------------
# チーム有利度計算
# --------------------------------------------
def calc_team_matchup_score(team, opponent_team, home_data):
    """チーム全体での相手に対する平均有利度"""
    total = 0
    count = 0

    for my_poke in team:
        my_data = home_data.get(my_poke, {})
        my_types = my_data.get("types", ["ノーマル"])
        usage = my_data.get("usage", 1.0)
        for opp in opponent_team:
            opp_data = home_data.get(opp, {})
            opp_types = opp_data.get("types", ["ノーマル"])
            adv = type_advantage(my_types, opp_types)
            total += adv * usage
            count += 1

    return total / max(count, 1)


# --------------------------------------------
# 役割バランス補正（攻撃・防御・素早さ）
# --------------------------------------------
def role_balance_score(team, home_data):
    atk_sum, spd_sum, def_sum = 0, 0, 0
    for name in team:
        d = home_data.get(name, {})
        s = d.get("stats", {})
        atk_sum += s.get("attack", 50)
        def_sum += s.get("defense", 50)
        spd_sum += s.get("speed", 50)
    return (atk_sum * 0.4 + def_sum * 0.3 + spd_sum * 0.3) / (len(team) * 100)


# --------------------------------------------
# 最適3体選出
# --------------------------------------------
def select_best_team():
    print("\n=== 選出AI 起動中 ===")

    team_data = safe_load_json(TEAM_JSON)
    home_data = safe_load_json(HOME_JSON)

    if not team_data:
        print("❌ 構築データが存在しません。先に build_team.py を実行してください。")
        return

    # 相手チーム例（次は自動入力化可能）
    opponent_team = ["オーガポン", "ミミッキュ", "ヒードラン"]
    print(f"\n📋 相手チーム: {', '.join(opponent_team)}")

    candidates = team_data if isinstance(team_data, list) else list(team_data.values())

    if len(candidates) < 3:
        print("❌ チームが3体未満です。")
        return

    # すべての3体組み合わせを評価
    scored = []
    for combo in combinations(candidates, 3):
        matchup = calc_team_matchup_score(combo, opponent_team, home_data)
        balance = role_balance_score(combo, home_data)
        total = matchup * 0.7 + balance * 0.3
        scored.append((combo, total))

    scored.sort(key=lambda x: x[1], reverse=True)
    best_team, best_score = scored[0]

    print("\n=== 最適選出結果 ===")
    for i, name in enumerate(best_team, 1):
        print(f"{i}. {name}")
    print(f"\n💡 総合スコア: {best_score:.3f}")

    # 保存
    safe_save_json(SELECT_JSON, list(best_team))
    print(f"💾 選出結果を保存しました → {SELECT_JSON}")


# --------------------------------------------
# 実行部
# --------------------------------------------
if __name__ == "__main__":
    select_best_team()