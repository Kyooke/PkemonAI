# ev_build_optimizer.py
# ============================================
# 🛠 EV & Build Optimizer
# バトルログから構築を進化させるツール
# ============================================

import os
import json
import math
from statistics import mean
from collections import defaultdict, Counter

DATA_DIR = "data"
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")
TEAM_JSON = os.path.join(DATA_DIR, "team.json")
BATTLE_LOG = os.path.join(DATA_DIR, "battle_log.json")
OUT_TEAM_JSON = os.path.join(DATA_DIR, "team_optimized.json")

# ---------- Helpers ----------
def safe_load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def safe_save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- Analysis ----------
def analyze_battle_logs():
    logs = safe_load_json(BATTLE_LOG)
    if not logs:
        print("⚠️ バトルログが見つからないか空です:", BATTLE_LOG)
        return None

    poke_stats = defaultdict(lambda: {
        "appearances": 0,
        "actions": 0,
        "damage_dealt": [],
        "hp_after": [],
        "opp_hp_after": [],
        "wins_when_present": 0,
        "battles_present": 0,
        "fainted_count": 0
    })

    for battle in logs:
        result = battle.get("result", "")
        turns = battle.get("turns", [])
        # collect which pokes appeared in this battle
        present = set()
        for t in turns:
            name = t.get("active")
            if not name:
                continue
            present.add(name)
            ps = poke_stats[name]
            ps["actions"] += 1
            ps["damage_dealt"].append(max(0, 100 - t.get("opp_hp_after", 100)))
            ps["hp_after"].append(t.get("hp_after", 0))
            ps["opp_hp_after"].append(t.get("opp_hp_after", 0))
            if t.get("hp_after", 0) <= 0:
                ps["fainted_count"] += 1

        for p in present:
            poke_stats[p]["appearances"] += 1
            poke_stats[p]["battles_present"] += 1
            if result == "win":
                poke_stats[p]["wins_when_present"] += 1

    # compute metrics
    metrics = {}
    for name, st in poke_stats.items():
        metrics[name] = {
            "appearances": st["appearances"],
            "avg_damage": mean(st["damage_dealt"]) if st["damage_dealt"] else 0,
            "avg_hp_after": mean(st["hp_after"]) if st["hp_after"] else 0,
            "avg_opp_hp_after": mean(st["opp_hp_after"]) if st["opp_hp_after"] else 0,
            "survival_rate": 0 if st["appearances"] == 0 else (st["appearances"]*1.0 - st["fainted_count"]) / st["appearances"],
            "win_rate_when_present": 0 if st["battles_present"] == 0 else st["wins_when_present"] / st["battles_present"],
            "fainted_count": st["fainted_count"]
        }
    return metrics

# ---------- Identify team weaknesses ----------
def detect_team_weaknesses(team, home_data, metrics):
    # team: list of pokemon names (team.json format can be list or dict)
    # home_data: mapping name->data
    names = team if isinstance(team, list) else list(team.keys())
    type_counters = Counter()
    role_counts = Counter()
    weak_types = Counter()

    # simple type count
    for n in names:
        types = home_data.get(n, {}).get("types", [])
        for t in types:
            type_counters[t] += 1

    # check low-survival and low-win pokes
    fragile = []
    underperform = []
    for n in names:
        m = metrics.get(n, {})
        if not m:
            continue
        if m.get("survival_rate", 1) < 0.5:
            fragile.append(n)
        if m.get("win_rate_when_present", 0) < 0.4 and m.get("appearances", 0) >= 2:
            underperform.append(n)

    # detect coverage gaps from common competitive types (example set)
    common_checks = ["electric", "water", "grass", "ice", "steel", "fairy", "ground", "fire"]
    for t in common_checks:
        if type_counters[t] == 0:
            weak_types[t] += 1

    weaknesses = {
        "type_counts": dict(type_counters),
        "fragile": fragile,
        "underperform": underperform,
        "type_gaps": list(weak_types.elements())
    }
    return weaknesses

# ---------- Candidate selection ----------
def candidate_replacements(weaknesses, team, home_data, top_n=5):
    # Suggest candidate picks from home_data to fill gaps
    names = set(team if isinstance(team, list) else list(team.keys()))
    candidates = []
    # score each home_data pokemon by: fills a type gap, has high win_rate or avg_damage, and not already in team
    for name, data in home_data.items():
        if name in names:
            continue
        types = data.get("types", [])
        score = 0
        # fills any gap
        for g in weaknesses.get("type_gaps", []):
            if g in types:
                score += 3
        # stat-based
        stats = data.get("stats", {})
        score += (stats.get("attack", 0) + stats.get("special-attack", 0)) / 200.0
        # prefer bulky picks if many fragile present
        if weaknesses.get("fragile") and (stats.get("hp", 0) > 90 or stats.get("defense", 0) > 90 or stats.get("special-defense", 0) > 90):
            score += 1.5
        candidates.append((name, score, types))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:top_n]

# ---------- EV & item suggestion ----------
def suggest_evs_and_item(name, home_data, metrics):
    base = home_data.get(name, {})
    stats = base.get("stats", {})
    role = "バランス"
    atk = stats.get("attack", 0)
    spa = stats.get("special-attack", 0)
    spd = stats.get("speed", 0)
    hp = stats.get("hp", 0)
    defense = stats.get("defense", 0)
    sdef = stats.get("special-defense", 0)

    # simple role guess
    if atk > spa and atk >= 100:
        role = "物理アタッカー"
    elif spa > atk and spa >= 100:
        role = "特殊アタッカー"
    elif (defense + sdef) > 200 or hp > 100:
        role = "耐久"
    elif spd > 110:
        role = "サポート"
    else:
        role = "バランス"

    evs = {"HP": 0, "攻撃": 0, "防御": 0, "特攻": 0, "特防": 0, "素早さ": 0}
    item = "たべのこし"

    # pick EVs by role
    if role == "物理アタッカー":
        evs = {"HP": 0, "攻撃": 252, "防御": 4, "特攻": 0, "特防": 0, "素早さ": 252}
        item = "こだわりハチマキ" if atk > 120 else "いのちのたま"
    elif role == "特殊アタッカー":
        evs = {"HP": 0, "攻撃": 0, "防御": 4, "特攻": 252, "特防": 0, "素早さ": 252}
        item = "こだわりメガネ" if spa > 120 else "いのちのたま"
    elif role == "耐久":
        evs = {"HP": 252, "攻撃": 0, "防御": 252, "特攻": 0, "特防": 4, "素早さ": 0}
        item = "たべのこし"
    elif role == "サポート":
        evs = {"HP": 252, "攻撃": 0, "防御": 0, "特攻": 0, "特防": 252, "素早さ": 4}
        item = "メンタルハーブ"
    else:
        evs = {"HP": 252, "攻撃": 0, "防御": 0, "特攻": 0, "特防": 4, "素早さ": 252}
        item = "いのちのたま"

    # small tweaks based on performance
    m = metrics.get(name, {})
    if m:
        if m.get("avg_damage", 0) < 20 and role in ("物理アタッカー", "特殊アタッカー"):
            # underperforming offense: move some HP -> Atk/SpA
            evs["HP"] = max(0, evs.get("HP", 0) - 52)
            if role == "物理アタッカー":
                evs["攻撃"] = min(252, evs.get("攻撃", 0) + 52)
            else:
                evs["特攻"] = min(252, evs.get("特攻", 0) + 52)
        if m.get("survival_rate", 1) < 0.5:
            evs["HP"] = min(252, evs.get("HP", 0) + 40)
            if role != "耐久":
                evs["防御"] = min(252, evs.get("防御", 0) + 20)

    # normalize to 510 or less
    total = sum(evs.values())
    if total > 510:
        scale = 510 / total
        for k in evs:
            evs[k] = int(evs[k] * scale)

    return {"role": role, "evs": evs, "item": item}

# ---------- Main optimizer ----------
def optimize_build(apply_changes=False):
    home_data = safe_load_json(HOME_JSON)
    if not home_data:
        print("❌ HOMEデータがありません:", HOME_JSON)
        return

    team_data = safe_load_json(TEAM_JSON)
    # support both formats: list of names OR dict name->build
    if isinstance(team_data, dict):
        team_names = list(team_data.keys())
    elif isinstance(team_data, list):
        team_names = team_data
    else:
        print("⚠️ team.json の形式が見慣れないです。listかdictにしてください。")
        return

    metrics = analyze_battle_logs()
    if metrics is None:
        return

    print("\n=== 📈 バトルログ解析結果（要約） ===")
    for n in team_names:
        m = metrics.get(n)
        if not m:
            print(f" - {n}: 出場なしまたはデータ不足")
            continue
        print(f" - {n}: 出場 {m['appearances']} 回 / 平均与ダメ {m['avg_damage']:.1f} / 生存率 {m['survival_rate']:.2f} / 勝率(出場時) {m['win_rate_when_present']:.2f}")

    weaknesses = detect_team_weaknesses(team_names, home_data, metrics)
    print("\n=== ⚠️ 構築の検出された課題 ===")
    print(" - 脆い枠:", weaknesses["fragile"])
    print(" - 成績不振枠:", weaknesses["underperform"])
    print(" - タイプ穴:", weaknesses["type_gaps"])

    # suggest replacements
    candidates = candidate_replacements(weaknesses, team_names, home_data, top_n=8)
    print("\n=== 🔁 交換候補（上位） ===")
    for i, (name, score, types) in enumerate(candidates, 1):
        print(f" {i}. {name} (score {score:.2f}, types {types})")

    # suggest EVs/items for current team
    suggestions = {}
    for n in team_names:
        suggestions[n] = suggest_evs_and_item(n, home_data, metrics)

    print("\n=== 🧾 個別のEV/持ち物提案 ===")
    for n, s in suggestions.items():
        print(f" - {n}: 役割 {s['role']}, 持ち物 {s['item']}, EVs {s['evs']}")

    # apply changes? ask user or apply programmatically
    if apply_changes:
        # build new team structure (dict with builds)
        new_team = {}
        for n in team_names:
            base = home_data.get(n, {})
            s = suggestions[n]
            # keep existing fields if team.json had dict
            build = {
                "types": base.get("types", []),
                "role": s["role"],
                "evs": s["evs"],
                "item": s["item"],
            }
            new_team[n] = build
        safe_save_json(OUT_TEAM_JSON, new_team)
        print(f"\n✅ 最適化チームを保存しました → {OUT_TEAM_JSON}")
    else:
        print("\nℹ️ apply_changes=False のためファイルは更新していません。保存するには apply_changes=True で実行してください。")

    return {
        "metrics": metrics,
        "weaknesses": weaknesses,
        "candidates": candidates,
        "suggestions": suggestions
    }

# ---------- CLI ----------
if __name__ == "__main__":
    print("=== EV & Build Optimizer ===")
    print("1) 分析のみ (default)")
    print("2) 分析して team_optimized.json を出力(apply)")
    c = input("番号を入力してください > ").strip()
    if c == "2":
        optimize_build(apply_changes=True)
    else:
        optimize_build(apply_changes=False)