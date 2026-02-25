# build_team.py
# ============================================
# 構築AI：シングル3vs3向け（個体最適化＋自動補完付き）
# ============================================

import os
import json
import random
from type_chart import TYPE_CHART
from input_home_data import get_pokemon_data  # ← PokéAPI補完に利用

DATA_DIR = "data"
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")
TEAM_JSON = os.path.join(DATA_DIR, "team.json")


# --------------------------------------------
# JSON安全読み書き
# --------------------------------------------
def safe_load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ {path} が壊れているため初期化します")
        return {}


def safe_save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --------------------------------------------
# 役割分類（種族値から自動推定）
# --------------------------------------------
def classify_role(stats):
    atk = stats.get("attack", 0)
    spa = stats.get("special-attack", 0)
    def_ = stats.get("defense", 0)
    spd = stats.get("special-defense", 0)
    spe = stats.get("speed", 0)

    if atk > spa and atk + spe > 250:
        return "物理アタッカー"
    elif spa > atk and spa + spe > 250:
        return "特殊アタッカー"
    elif def_ + spd > 230:
        return "タンク"
    else:
        return "サポート"


# --------------------------------------------
# 努力値割り当て
# --------------------------------------------
def assign_evs(role):
    if role == "物理アタッカー":
        return {"HP": 4, "攻撃": 252, "防御": 0, "特攻": 0, "特防": 0, "素早さ": 252}
    elif role == "特殊アタッカー":
        return {"HP": 4, "攻撃": 0, "防御": 0, "特攻": 252, "特防": 0, "素早さ": 252}
    elif role == "タンク":
        return {"HP": 252, "攻撃": 0, "防御": 156, "特攻": 0, "特防": 100, "素早さ": 0}
    else:
        return {"HP": 252, "攻撃": 0, "防御": 0, "特攻": 0, "特防": 252, "素早さ": 4}


# --------------------------------------------
# 性格決定
# --------------------------------------------
def assign_nature(role):
    if role == "物理アタッカー":
        return "いじっぱり"
    elif role == "特殊アタッカー":
        return "ひかえめ"
    elif role == "タンク":
        return "ずぶとい"
    else:
        return "おだやか"


# --------------------------------------------
# 持ち物割り当て（重複防止）
# --------------------------------------------
ITEM_POOL = [
    "こだわりスカーフ", "こだわりハチマキ", "とつげきチョッキ",
    "いのちのたま", "たべのこし", "きあいのタスキ",
    "ゴツゴツメット", "ラムのみ", "オボンのみ"
]

def assign_item(used_items, role):
    preferred = {
        "物理アタッカー": ["こだわりハチマキ", "いのちのたま", "きあいのタスキ"],
        "特殊アタッカー": ["こだわりスカーフ", "いのちのたま", "きあいのタスキ"],
        "タンク": ["たべのこし", "ゴツゴツメット", "オボンのみ"],
        "サポート": ["オボンのみ", "ラムのみ", "たべのこし"],
    }.get(role, [])

    for item in preferred:
        if item not in used_items:
            used_items.add(item)
            return item

    for item in ITEM_POOL:
        if item not in used_items:
            used_items.add(item)
            return item
    return "なし"


# --------------------------------------------
# 技構成自動生成
# --------------------------------------------
def select_moves(types, role):
    offensive_moves = {
        "ほのお": ["フレアドライブ", "かえんほうしゃ", "オーバーヒート"],
        "みず": ["ハイドロポンプ", "なみのり", "アクアジェット"],
        "でんき": ["１０まんボルト", "ボルトチェンジ", "ワイルドボルト"],
        "くさ": ["リーフストーム", "ギガドレイン", "やどりぎのタネ"],
        "こおり": ["れいとうビーム", "つららばり", "フリーズドライ"],
        "かくとう": ["インファイト", "ドレインパンチ"],
        "どく": ["ヘドロウェーブ", "ダストシュート"],
        "じめん": ["じしん", "じならし"],
        "ひこう": ["ブレイブバード", "エアスラッシュ"],
        "エスパー": ["サイコキネシス", "めいそう"],
        "むし": ["とんぼがえり", "シザークロス"],
        "いわ": ["ストーンエッジ", "がんせきふうじ"],
        "ゴースト": ["シャドーボール", "シャドークロー"],
        "ドラゴン": ["げきりん", "りゅうせいぐん"],
        "あく": ["かみくだく", "バークアウト"],
        "はがね": ["アイアンヘッド", "ラスターカノン"],
        "フェアリー": ["ムーンフォース", "じゃれつく"],
        "ノーマル": ["すてみタックル", "からげんき"]
    }

    support_moves = ["まもる", "でんじは", "つるぎのまい", "わるだくみ", "ビルドアップ"]

    move_pool = []
    for t in types:
        move_pool.extend(offensive_moves.get(t, []))

    if not move_pool:
        move_pool = ["たいあたり"]

    random.shuffle(move_pool)
    moves = move_pool[:3]  # 攻撃技3つ
    moves.append(random.choice(support_moves))
    return moves


# --------------------------------------------
# 相性スコア
# --------------------------------------------
def type_matchup_score(types_list):
    score = 0.0
    for atk_type, effects in TYPE_CHART.items():
        total = sum(effects.get(t, 1.0) for t in types_list)
        avg = total / len(types_list)
        if avg < 1:
            score += 1.0
        elif avg > 1:
            score -= 0.5
    return score


# --------------------------------------------
# ポケモン評価スコア
# --------------------------------------------
def calc_pokemon_score(pokemon_data):
    types = pokemon_data.get("types", [])
    stats = pokemon_data.get("stats", {})
    usage = pokemon_data.get("usage", 1.0)

    atk = stats.get("attack", 50)
    spe = stats.get("speed", 50)
    spa = stats.get("special-attack", 50)

    base = (atk * 0.55 + spa * 0.25 + spe * 0.2) / 10
    return base + type_matchup_score(types) + usage / 10


# --------------------------------------------
# 構築生成メイン
# --------------------------------------------
def build_team():
    print("\n=== 構築生成モード（自動補完付き） ===")

    home_data = safe_load_json(HOME_JSON)

    # --- PokéAPIで自動補完 ---
    if len(home_data) < 6:
        print(f"⚠️ HOMEデータが少ないため、自動補完を開始します ({len(home_data)}件)")
        default_list = [
            "カイリュー", "ドドゲザン", "サーフゴー",
            "テツノツツミ", "モロバレル", "ハバタクカミ"
        ]
        for name in default_list:
            if name not in home_data:
                data = get_pokemon_data(name)
                if data:
                    home_data[name] = data
                    print(f"✅ {name} を自動登録しました")
        safe_save_json(HOME_JSON, home_data)

    # --- 構築生成 ---
    scored = [(n, calc_pokemon_score(d), d) for n, d in home_data.items()]
    scored.sort(key=lambda x: x[1], reverse=True)

    selected = []
    used_types = set()
    used_items = set()

    for name, score, data in scored:
        if len(selected) >= 6:
            break

        types = tuple(sorted(data.get("types", [])))
        overlap = sum(t in used_types for t in types)

        if overlap >= 2 and len(selected) >= 4:
            continue

        role = classify_role(data.get("stats", {}))
        evs = assign_evs(role)
        nature = assign_nature(role)
        item = assign_item(used_items, role)
        moves = select_moves(data.get("types", []), role)

        selected.append({
            "name": name,
            "score": round(score, 2),
            "role": role,
            "types": data.get("types", []),
            "nature": nature,
            "item": item,
            "evs": evs,
            "moves": moves
        })
        used_types.update(types)

    print("\n=== 構築結果 ===")
    for p in selected:
        print(f" - {p['name']}（{p['role']}） 持ち物:{p['item']} 性格:{p['nature']}")
        print(f"   技: {', '.join(p['moves'])}")

    safe_save_json(TEAM_JSON, {"rule": "single", "team": selected})
    print(f"\n💾 構築データを保存しました → {TEAM_JSON}")


# --------------------------------------------
# 実行部
# --------------------------------------------
if __name__ == "__main__":
    build_team()