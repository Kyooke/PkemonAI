# ============================================
# 🧱 build_team.py
# 主軸中心＋役割補完AI（タイプ柔軟・6体保証・自動補完版）
# ============================================

import os
import json
import random
from glob import glob
from type_chart import TYPE_CHART
from input_home_data import safe_load_json, safe_save_json, get_pokemon_data

DATA_DIR = "data"
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")
TEAM_JSON = os.path.join(DATA_DIR, "team.json")
ARTICLE_DIR = os.path.join(DATA_DIR, "articles")
LOG_PATH = os.path.join(DATA_DIR, "battle_log.json")

# -------------------------------------------------
def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

# -------------------------------------------------
def classify_role(stats):
    atk = stats.get("attack", 0)
    sp_atk = stats.get("special-attack", 0)
    defn = stats.get("defense", 0)
    sp_def = stats.get("special-defense", 0)
    speed = stats.get("speed", 0)
    hp = stats.get("hp", 0)

    if atk > 120 and speed > 80:
        return "物理アタッカー"
    if sp_atk > 120 and speed > 80:
        return "特殊アタッカー"
    if hp > 90 and (defn + sp_def) > 200:
        return "受け"
    if speed > 110 and (atk + sp_atk) < 150:
        return "サポート"
    if atk > 100 and sp_atk > 100:
        return "積みアタッカー"
    return "バランス"

# -------------------------------------------------
def load_article_and_logs():
    trends, win_bonus = {}, {}
    for path in glob(os.path.join(ARTICLE_DIR, "*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                art = json.load(f)
                for p in art.get("team", []):
                    name = p["name"]
                    trends[name] = trends.get(name, 0) + 1
        except:
            continue

    log = load_json(LOG_PATH)
    if isinstance(log, list):
        for b in log:
            if b.get("result") == "win":
                for poke in b.get("opponent", []):
                    win_bonus[poke] = win_bonus.get(poke, 0) + 1
    return trends, win_bonus

# -------------------------------------------------
def build_team():
    print("\n=== 🧱 主軸＋役割補完構築生成AI（6体保証） ===")

    home_data = safe_load_json(HOME_JSON)
    if not home_data:
        print("❌ HOMEデータがありません。")
        return

    trends, win_bonus = load_article_and_logs()

    # === 主軸選定 ===
    core_input = input("主軸にしたいポケモン名を入力（空で自動選択）> ").strip()
    if core_input and core_input in home_data:
        core_pokemon = core_input
    else:
        core_pokemon = max(
            home_data.items(),
            key=lambda x: (
                x[1]["stats"].get("attack", 0)
                + x[1]["stats"].get("special-attack", 0)
                + trends.get(x[0], 0) * 8
                + win_bonus.get(x[0], 0) * 5
            ),
        )[0]
    print(f"🎯 主軸ポケモン: {core_pokemon}")

    # === 主軸情報 ===
    core_data = home_data[core_pokemon]
    core_types = core_data.get("types", ["不明"])
    core_role = classify_role(core_data.get("stats", {}))
    print(f"🧩 主軸の役割: {core_role} / タイプ: {core_types}")

    # === 補完候補 ===
    scored = []
    for name, data in home_data.items():
        if name == core_pokemon:
            continue
        types = data.get("types", ["不明"])
        role = classify_role(data.get("stats", {}))
        synergy = sum(
            1.0 if TYPE_CHART.get(t1, {}).get(t2, 1.0) < 1.0 else 0.0
            for t1 in types for t2 in core_types
        )
        trend = trends.get(name, 0)
        win = win_bonus.get(name, 0)
        diversity = 1.5 if role != core_role else 0.8
        score = synergy * 2.0 + trend * 1.8 + win * 1.3 + diversity
        scored.append((name, role, score))

    scored.sort(key=lambda x: x[2], reverse=True)

    # === 構築作成 ===
    team = [core_pokemon]
    used_roles = {core_role}
    used_items = {core_data.get("item", "")}
    type_count = {t: 1 for t in core_types if t != "不明"}

    for name, role, _ in scored:
        if len(team) >= 6:
            break
        data = home_data[name]
        item = data.get("item", "")
        types = data.get("types", ["不明"])

        # 同じ持ち物禁止
        if item in used_items:
            continue

        # タイプ被りは「2体まで許可」
        if any(type_count.get(t, 0) >= 2 for t in types if t != "不明"):
            continue

        team.append(name)
        used_roles.add(role)
        used_items.add(item)
        for t in types:
            if t != "不明":
                type_count[t] = type_count.get(t, 0) + 1

    # === 足りない場合はスコア順補充 ===
    if len(team) < 6:
        print(f"⚠️ 補完候補が不足（{len(team)}体）。スコア順で補充します。")
        for name, _, _ in scored:
            if len(team) >= 6:
                break
            if name not in team:
                team.append(name)

    # === タイプ不明 or 持ち物未設定補完 ===
    for t in team:
        data = home_data[t]
        if "types" not in data or "不明" in data["types"]:
            fixed = get_pokemon_data(t)
            if fixed:
                home_data[t] = fixed
        if not data.get("item"):
            data["item"] = random.choice(["こだわりスカーフ", "いのちのたま", "たべのこし"])

    safe_save_json(TEAM_JSON, team)

    print("\n✅ 構築完成:")
    for t in team:
        d = home_data.get(t, {})
        print(f"  - {t} ({', '.join(d.get('types', ['不明']))}) [{d.get('item', '未設定')}]")
    print(f"\n💾 保存先: {TEAM_JSON}")

# -------------------------------------------------
if __name__ == "__main__":
    build_team()