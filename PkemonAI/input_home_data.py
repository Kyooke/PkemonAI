# =========================================
# input_home_data.py
# PokéAPI連携 + 日本語対応 + 自動英訳キャッシュ対応版
# =========================================

import os
import json
import random
import requests

DATA_DIR = "data"
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")
NAME_MAP_JSON = os.path.join(DATA_DIR, "name_map.json")

# -------------------------------------------------
# JSON セーフ読み書き
# -------------------------------------------------
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

# -------------------------------------------------
# 日本語 → 英語変換（辞書＋キャッシュ＋PokéAPI自動英訳）
# -------------------------------------------------
def jp_to_en(name_ja):
    """日本語ポケモン名 → 英語名変換（キャッシュ学習対応）"""
    # キャッシュ読み込み
    name_map = safe_load_json(NAME_MAP_JSON)

    # キャッシュにある場合
    if name_ja in name_map:
        return name_map[name_ja]

    # 固定辞書（よく使うもの）
    fixed_map = {
        "カイリュー": "dragonite", "サーフゴー": "gholdengo", "ドドゲザン": "kingambit",
        "テツノツツミ": "iron-bundle", "モロバレル": "amoonguss", "ハバタクカミ": "flutter-mane",
        "パオジアン": "chien-pao", "ディンルー": "ting-lu", "イーユイ": "chi-yu", "チオンジェン": "wo-chien",
        "ママンボウ": "alomomola", "グライオン": "gliscor", "ボーマンダ": "salamence", "バンギラス": "tyranitar",
        "レックウザ": "rayquaza", "ザシアン": "zacian", "ザマゼンタ": "zamazenta",
        "ミライドン": "miraidon", "コライドン": "koraidon", "ソルガレオ": "solgaleo", "ルナアーラ": "lunala",
    }

    if name_ja in fixed_map:
        name_map[name_ja] = fixed_map[name_ja]
        safe_save_json(NAME_MAP_JSON, name_map)
        return fixed_map[name_ja]

    # PokéAPIで自動検索
    print(f"🔍 {name_ja} の英語名をPokéAPIから検索中...")
    try:
        for i in range(1, 1026):  # 1〜1000体以上対応
            species_url = f"https://pokeapi.co/api/v2/pokemon-species/{i}"
            res = requests.get(species_url)
            if res.status_code != 200:
                continue
            data = res.json()
            names = data.get("names", [])
            ja_name = next((n["name"] for n in names if n["language"]["name"] in ["ja", "ja-Hrkt"]), None)
            en_name = next((n["name"] for n in names if n["language"]["name"] == "en"), None)
            if ja_name == name_ja and en_name:
                en_name = en_name.lower()
                print(f"✅ 自動変換成功: {name_ja} → {en_name}")
                name_map[name_ja] = en_name
                safe_save_json(NAME_MAP_JSON, name_map)
                return en_name
    except Exception as e:
        print(f"⚠️ 自動英訳中にエラー発生: {e}")

    # 失敗時はローマ字変換
    en_name = name_ja.lower()
    print(f"⚠️ {name_ja} の英訳が見つからなかったため暫定登録 → {en_name}")
    name_map[name_ja] = en_name
    safe_save_json(NAME_MAP_JSON, name_map)
    return en_name

# -------------------------------------------------
# アイテム・性格・努力値生成
# -------------------------------------------------
def generate_random_item(poke_type):
    items = [
        "こだわりスカーフ", "いのちのたま", "きあいのタスキ",
        "たべのこし", "ゴツゴツメット", "おんみつマント", "ラムのみ"
    ]
    return random.choice(items)

def generate_random_nature():
    natures = ["ようき", "いじっぱり", "おくびょう", "ひかえめ", "ずぶとい", "おだやか"]
    return random.choice(natures)

def generate_random_evs():
    ev_patterns = [
        {"HP": 0, "攻撃": 252, "防御": 0, "特攻": 0, "特防": 4, "素早さ": 252},
        {"HP": 252, "攻撃": 0, "防御": 4, "特攻": 0, "特防": 252, "素早さ": 0},
        {"HP": 252, "攻撃": 0, "防御": 252, "特攻": 0, "特防": 4, "素早さ": 0},
    ]
    return random.choice(ev_patterns)

# -------------------------------------------------
# PokéAPIからポケモンデータ取得
# -------------------------------------------------
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

    types = [t["type"]["name"] for t in data["types"]]
    stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
    moves = [m["move"]["name"] for m in data["moves"]]

    return {
        "types": types,
        "stats": stats,
        "moves": random.sample(moves, min(4, len(moves))),
        "item": generate_random_item(types[0]),
        "nature": generate_random_nature(),
        "evs": generate_random_evs(),
    }

# -------------------------------------------------
# HOMEデータ更新
# -------------------------------------------------
def update_home_data(pokemon_names):
    home_data = safe_load_json(HOME_JSON)
    for name in pokemon_names:
        data = get_pokemon_data(name)
        if data:
            home_data[name] = data
    safe_save_json(HOME_JSON, home_data)
    print(f"✅ HOMEデータを保存しました ({len(home_data)}件)")

# -------------------------------------------------
# 実行部
# -------------------------------------------------
if __name__ == "__main__":
    print("=== 🏠 PokéAPI + 英訳キャッシュ テスト ===")
    update_home_data(["ジバコイル", "ウーラオス", "カイリュー"])