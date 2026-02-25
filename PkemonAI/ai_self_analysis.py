# ai_self_analysis.py
# ============================================
# バトルログを分析し、構築変更が必要かを自動判断するAI
# ============================================

import os
import json
import random
from type_chart import TYPE_CHART
from build_team import build_team, safe_load_json, safe_save_json


DATA_DIR = "data"
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")
TEAM_JSON = os.path.join(DATA_DIR, "team.json")
LOG_JSON = os.path.join(DATA_DIR, "battle_log.json")


# --------------------------------------------
# バトルログ読み込み
# --------------------------------------------
def load_logs():
    if not os.path.exists(LOG_JSON):
        return []
    with open(LOG_JSON, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


# --------------------------------------------
# 勝率・敗因の傾向を分析
# --------------------------------------------
def analyze_performance(logs):
    total, wins = 0, 0
    weakness_counter = {}
    for record in logs:
        total += 1
        if record["result"] == "win":
            wins += 1
        else:
            for opp in record.get("opponent", []):
                weakness_counter[opp] = weakness_counter.get(opp, 0) + 1
    winrate = wins / max(total, 1)
    return winrate, weakness_counter


# --------------------------------------------
# 苦手機体タイプを推定
# --------------------------------------------
def find_weak_types(weakness_counter, home_data):
    type_count = {}
    for opp_name in weakness_counter.keys():
        t = home_data.get(opp_name, {}).get("types", [])
        for typ in t:
            type_count[typ] = type_count.get(typ, 0) + 1
    return sorted(type_count.items(), key=lambda x: x[1], reverse=True)


# --------------------------------------------
# 自己判断ロジック
# --------------------------------------------
def self_evaluate_and_rebuild():
    print("\n=== 自己分析AI（構築維持・調整判定） ===")

    logs = load_logs()
    if not logs:
        print("⚠️ バトルログがありません。初期構築を維持します。")
        return

    home_data = safe_load_json(HOME_JSON)
    winrate, weakness_counter = analyze_performance(logs)
    weak_types = find_weak_types(weakness_counter, home_data)

    print(f"📊 現在の勝率: {winrate*100:.1f}%")
    if weak_types:
        print("💀 苦手機体タイプ:", ", ".join([f"{t}×{n}" for t, n in weak_types[:3]]))

    # 構築維持・変更判定ロジック
    if winrate >= 0.6:
        print("✅ 勝率良好：構築維持します。")
        return
    elif winrate < 0.4 and weak_types:
        print("⚠️ 勝率低下：部分的に構築を再生成します。")
        adjust_team(weak_types[:2], home_data)
    else:
        print("🤔 微調整不要：プレイング改善が優先です。")


# --------------------------------------------
# 部分構築調整（苦手タイプ補完）
# --------------------------------------------
def adjust_team(weak_types, home_data):
    team = safe_load_json(TEAM_JSON)
    if not team:
        print("❌ 現在の構築が見つかりません。再生成します。")
        build_team()
        return

    print("🔧 弱点補完中...")
    candidates = []

    for name, data in home_data.items():
        t = data.get("types", [])
        for wt, _ in weak_types:
            # 弱点タイプに強いタイプを探す
            for atk, chart in TYPE_CHART.items():
                if chart.get(wt, 1.0) > 1.0 and atk in t:
                    candidates.append(name)

    # ランダムで差し替え（最大2体）
    replace_count = min(2, len(candidates))
    for _ in range(replace_count):
        old = random.choice(team)
        new = random.choice(candidates)
        team.remove(old)
        team.append(new)
        print(f"🧩 {old} → {new} に交代")

    safe_save_json(TEAM_JSON, team)
    print(f"💾 構築を更新しました → {TEAM_JSON}")
