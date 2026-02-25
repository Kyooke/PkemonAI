# analyze_battle.py
# === バトルログ解析モジュール ===
# 入力: data/battle_log.json
# 出力: data/battle_features.json, data/analysis_summary.txt

import os
import json
import math
import statistics
from collections import Counter, defaultdict

DATA_DIR = "data"
BATTLE_LOG = os.path.join(DATA_DIR, "battle_log.json")
FEATURES_OUT = os.path.join(DATA_DIR, "battle_features.json")
SUMMARY_OUT = os.path.join(DATA_DIR, "analysis_summary.txt")


def load_battle_logs(path):
    if not os.path.exists(path):
        print(f"❌ ログが見つかりません: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            logs = json.load(f)
            if isinstance(logs, dict):
                # もし単一ログが辞書で保存されている場合はリスト化
                logs = [logs]
            return logs
        except Exception as e:
            print("❌ ログの読み込みに失敗しました:", e)
            return []


def safe_get(d, *keys, default=None):
    cur = d
    try:
        for k in keys:
            cur = cur[k]
        return cur
    except Exception:
        return default


def features_from_single_log(record):
    # record は対戦1件分
    turns = record.get("turns", []) or []
    my_team = record.get("my_team", []) or []
    opponent = record.get("opponent", []) or []
    result = record.get("result", "").lower()
    timestamp = record.get("timestamp", record.get("time", None))

    f = {}
    f["timestamp"] = timestamp
    f["result"] = result
    f["my_team"] = my_team
    f["opponent_team"] = opponent
    f["turn_count"] = len(turns)

    # counters and accumulators
    attack_count = 0
    protect_count = 0
    switch_count = 0
    sacrifice_count = 0
    move_counter = Counter()
    damage_done_total = 0.0
    damage_taken_total = 0.0
    hp_after_my = []
    hp_after_opp = []
    first_turn_action = None
    uturn_like_count = 0

    for i, t in enumerate(turns):
        action = t.get("action", "") or ""
        # normalize "attack:技名" -> attack
        if isinstance(action, str) and action.startswith("attack:"):
            move = action.split("attack:", 1)[1]
            move_counter[move] += 1
            attack_count += 1
        elif isinstance(action, str) and action.startswith("use_u_turn"):
            # some logs used other naming
            uturn_like_count += 1
            switch_count += 1
        else:
            # classify common labels
            if action == "attack" or action.startswith("attack"):
                attack_count += 1
            elif action == "protect" or "protect" in action:
                protect_count += 1
            elif action == "switch" or action.startswith("switch"):
                switch_count += 1
            elif action == "sacrifice" or action == "sacrifice":
                sacrifice_count += 1
            else:
                # try detecting move names in action string
                if isinstance(action, str) and ":" in action:
                    # e.g. action = "attack:とんぼがえり"
                    parts = action.split(":")
                    if len(parts) >= 2:
                        mv = parts[1]
                        move_counter[mv] += 1
                        attack_count += 1

        # damage fields (varying formats)
        dmg_done = safe_get(t, "damage_done", default=None)
        if dmg_done is None:
            # try other keys
            dmg_done = safe_get(t, "damage", default=0) or 0
        if isinstance(dmg_done, (int, float)):
            damage_done_total += float(dmg_done)

        dmg_taken = safe_get(t, "damage_taken", default=None)
        if dmg_taken is None:
            dmg_taken = safe_get(t, "taken", default=0) or 0
        if isinstance(dmg_taken, (int, float)):
            damage_taken_total += float(dmg_taken)

        my_hp_after = safe_get(t, "hp_after", default=None)
        opp_hp_after = safe_get(t, "opp_hp_after", default=None)
        if isinstance(my_hp_after, (int, float)):
            hp_after_my.append(float(my_hp_after))
        if isinstance(opp_hp_after, (int, float)):
            hp_after_opp.append(float(opp_hp_after))

        # first turn action
        if i == 0 and first_turn_action is None:
            first_turn_action = action

        # detect u-turn style moves in move names
        if isinstance(action, str):
            if any(u in action for u in ["とんぼ", "ボルトチェンジ", "とんぼがえり", "ボルトチェンジ"]):
                uturn_like_count += 1

    f["attack_count"] = attack_count
    f["protect_count"] = protect_count
    f["switch_count"] = switch_count
    f["sacrifice_count"] = sacrifice_count
    f["unique_moves_used"] = dict(move_counter)
    f["total_damage_done"] = round(damage_done_total, 3)
    f["total_damage_taken"] = round(damage_taken_total, 3)
    f["avg_my_hp_after"] = round(statistics.mean(hp_after_my), 3) if hp_after_my else None
    f["avg_opp_hp_after"] = round(statistics.mean(hp_after_opp), 3) if hp_after_opp else None
    f["first_turn_action"] = first_turn_action
    f["uturn_like_count"] = uturn_like_count

    # derived metrics
    f["attack_ratio"] = round(attack_count / f["turn_count"], 3) if f["turn_count"] > 0 else 0.0
    f["switch_ratio"] = round(switch_count / f["turn_count"], 3) if f["turn_count"] > 0 else 0.0
    f["sacrifice_ratio"] = round(sacrifice_count / f["turn_count"], 3) if f["turn_count"] > 0 else 0.0
    f["damage_per_turn"] = round(damage_done_total / f["turn_count"], 3) if f["turn_count"] > 0 else 0.0

    return f


def aggregate_features(feature_list):
    agg = {}
    n = len(feature_list)
    if n == 0:
        return agg
    wins = sum(1 for f in feature_list if f.get("result") == "win")
    losses = sum(1 for f in feature_list if f.get("result") == "lose")
    draws = sum(1 for f in feature_list if f.get("result") == "draw")
    agg["battle_count"] = n
    agg["win_rate"] = round(wins / n * 100, 2)
    agg["loss_rate"] = round(losses / n * 100, 2)
    agg["draw_rate"] = round(draws / n * 100, 2)
    agg["avg_turns"] = round(statistics.mean([f["turn_count"] for f in feature_list]), 2)
    agg["median_turns"] = statistics.median([f["turn_count"] for f in feature_list])
    agg["avg_damage_per_turn"] = round(statistics.mean([f.get("damage_per_turn", 0.0) for f in feature_list]), 3)
    agg["avg_switch_ratio"] = round(statistics.mean([f.get("switch_ratio", 0.0) for f in feature_list]), 3)
    agg["avg_attack_ratio"] = round(statistics.mean([f.get("attack_ratio", 0.0) for f in feature_list]), 3)
    agg["avg_sacrifice_ratio"] = round(statistics.mean([f.get("sacrifice_ratio", 0.0) for f in feature_list]), 3)

    # common moves overall
    move_counter = Counter()
    for f in feature_list:
        move_counter.update(f.get("unique_moves_used", {}))
    most_common_moves = move_counter.most_common(10)
    agg["most_common_moves"] = most_common_moves

    # heuristic issues detection
    issues = []
    if agg["win_rate"] < 45.0:
        issues.append("勝率が低めです（<45%）。プレイング改善を優先してください。")
    if agg["avg_switch_ratio"] > 0.35:
        issues.append("交代率が高めです。安定した対面維持で試合を長引かせすぎている可能性があります。")
    if agg["avg_attack_ratio"] < 0.4:
        issues.append("攻撃率が低めです。攻めの選択が不足している可能性があります。")
    if agg["avg_damage_per_turn"] < 10.0:
        issues.append("1ターンあたりの平均火力が低めです。構築か技選択を見直してください。")

    agg["issues"] = issues
    return agg


def generate_text_summary(agg, feature_list):
    if not agg:
        return "ログが見つかりませんでした。対戦ログを `data/battle_log.json` に配置してください。"

    lines = []
    lines.append("=== 対戦ログ解析サマリ ===")
    lines.append(f"解析対象試合数: {agg['battle_count']}")
    lines.append(f"勝率: {agg['win_rate']}%（負け: {agg['loss_rate']}% / 引き分け: {agg['draw_rate']}%）")
    lines.append(f"平均ターン数: {agg['avg_turns']}（中央値: {agg['median_turns']}）")
    lines.append(f"平均ダメージ/ターン: {agg['avg_damage_per_turn']}")
    lines.append(f"平均交代率: {agg['avg_switch_ratio']}")
    lines.append(f"平均攻撃率: {agg['avg_attack_ratio']}")
    lines.append("よく使われる技（上位10）:")
    for mv, cnt in agg["most_common_moves"]:
        lines.append(f"  - {mv}: {cnt} 回")

    lines.append("\n自動検出された改善点（ヒューリスティック）:")
    if agg["issues"]:
        for it in agg["issues"]:
            lines.append(f"  - {it}")
    else:
        lines.append("  - 目立った問題は検出されませんでした。")

    # 例: 直近5試合の傾向
    recent = feature_list[-5:]
    lines.append("\n直近5試合の簡易レポート:")
    for idx, f in enumerate(recent, 1):
        lines.append(f"  試合-{idx}: 結果={f.get('result')}, ターン={f.get('turn_count')}, 攻撃数={f.get('attack_count')}, 交代数={f.get('switch_count')}, 火力/turn={f.get('damage_per_turn')}")

    return "\n".join(lines)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    logs = load_battle_logs(BATTLE_LOG)
    if not logs:
        print("解析を終了します（ログなし）。")
        return

    features = []
    for rec in logs:
        f = features_from_single_log(rec)
        features.append(f)

    agg = aggregate_features(features)
    summary_text = generate_text_summary(agg, features)

    # 保存
    save_json(FEATURES_OUT, {"features": features, "aggregate": agg})
    with open(SUMMARY_OUT, "w", encoding="utf-8") as s:
        s.write(summary_text)

    print("✅ 解析完了。出力:")
    print(f" - 特徴量: {FEATURES_OUT}")
    print(f" - サマリ: {SUMMARY_OUT}")
    print("\n--- サマリ（一部） ---\n")
    print(summary_text[:2000])  # 先頭一部表示


if __name__ == "__main__":
    main()