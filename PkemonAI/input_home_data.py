# input_home_data.py
# =========================================
# PokéAPI連携 + 日本語タイプ変換対応版
# =========================================

import os
import json
import random
import requests

DATA_DIR = "data"
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")

# =========================================
# JSON安全読み書き
# =========================================
def safe_load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ {path} が空または壊れているため初期化します")
        return {}

def safe_save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================================
# 日本語→英語変換
# =========================================
def jp_to_en(name_ja):
    name_map = {
        "ドドゲザン": "kingambit",
        "サーフゴー": "gholdengo",
        "カイリュー": "dragonite",
        "テツノツツミ": "iron-bundle",
        "モロバレル": "amoonguss",
        "リザードン": "charizard",
        "ミミッキュ": "mimikyu",
        "ガブリアス": "garchomp",
        "ドラパルト": "dragapult",
        "ハバタクカミ": "flutter-mane",
        "パオジアン": "chien-pao",
    }
    return name_map.get(name_ja, name_ja.lower())

# =========================================
# 英語→日本語タイプ変換
# =========================================
def en_to_jp_type(type_en):
    table = {
        "normal": "ノーマル", "fire": "ほのお", "water": "みず", "electric": "でんき",
        "grass": "くさ", "ice": "こおり", "fighting": "かくとう", "poison": "どく",
        "ground": "じめん", "flying": "ひこう", "psychic": "エスパー", "bug": "むし",
        "rock": "いわ", "ghost": "ゴースト", "dragon": "ドラゴン", "dark": "あく",
        "steel": "はがね", "fairy": "フェアリー"
    }
    return table.get(type_en.lower(), type_en)

# =========================================
# AI補完（性格・努力値・持ち物）
# =========================================
def generate_random_item(poke_type):
    items = [
        "こだわりスカーフ", "こだわりハチマキ", "たべのこし",
        "とつげきチョッキ", "いのちのたま", "きあいのタスキ", "ゴツゴツメット"
    ]
    return random.choice(items)

def generate_random_nature():
    natures = ["ようき", "いじっぱり", "おくびょう", "ひかえめ", "ずぶとい", "おだやか"]
    return random.choice(natures)

def generate_random_evs():
    return {
        "HP": random.choice([0, 252]),
        "攻撃": random.choice([0, 252]),
        "防御": random.choice([0, 252]),
        "特攻": random.choice([0, 252]),
        "特防": random.choice([0, 252]),
        "素早さ": random.choice([0, 252]),
    }

# =========================================
# PokéAPIからデータ取得
# =========================================
def get_pokemon_data(name_ja):
    name_en = jp_to_en(name_ja)
    url = f"https://pokeapi.co/api/v2/pokemon/{name_en}"

    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
    except Exception:
        print(f"❌ PokéAPI取得失敗: {name_ja} ({url})")
        return None

    # ✅ 英語タイプ名 → 日本語タイプ名に変換
    types = [en_to_jp_type(t["type"]["name"]) for t in data["types"]]
    stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
    moves = [m["move"]["name"] for m in data["moves"]]
    abilities = [a["ability"]["name"] for a in data["abilities"]]

    return {
        "types": types,
        "stats": stats,
        "abilities": abilities,
        "moves": random.sample(moves, min(4, len(moves))),
        "item": generate_random_item(types[0]),
        "nature": generate_random_nature(),
        "evs": generate_random_evs(),
        "usage": random.uniform(1, 20),
    }

# =========================================
# HOMEデータ更新
# =========================================
def update_home_data(pokemon_names):
    home_data = safe_load_json(HOME_JSON)
    for name in pokemon_names:
        data = get_pokemon_data(name)
        if data:
            home_data[name] = data
            print(f"✅ {name} を更新しました")
    safe_save_json(HOME_JSON, home_data)
    print(f"\n💾 HOMEデータを保存しました ({len(home_data)}件) → {HOME_JSON}")

# =========================================
# 実行部
# =========================================
if __name__ == "__main__":
    print("=== PokéAPI連携版 HOMEデータ更新 ===")
    team = ["ドドゲザン", "サーフゴー", "カイリュー", "テツノツツミ", "モロバレル"]
    update_home_data(team)