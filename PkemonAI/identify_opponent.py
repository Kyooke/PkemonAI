# identify_opponent.py
# ============================================
# 相手ポケモン種別特定AI（ニックネーム対応＋PokéAPI＋HOME連携）
# ============================================

import os
import json
import requests
from input_home_data import jp_to_en, get_pokemon_data, safe_save_json, safe_load_json

DATA_DIR = "data"
NICK_MAP = os.path.join(DATA_DIR, "nickname_map.json")
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")


# ===== JSON Utility =====
def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def safe_save(path, data):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def safe_load(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


# ===== メイン関数 =====
def resolve_opponent_name(ocr_name):
    """
    OCRで得た相手ポケモン名（ニックネーム含む）から、
    正式な種族名を特定し、home_data.jsonに自動登録。
    """
    nick_cache = safe_load(NICK_MAP)
    home_data = safe_load(HOME_JSON)

    # 1️⃣ 既存キャッシュ
    if ocr_name in nick_cache:
        species = nick_cache[ocr_name]
        print(f"✅ キャッシュ命中: {ocr_name} → {species}")
        return species

    # 2️⃣ PokéAPI照会（正式名 or 英名）
    name_en = jp_to_en(ocr_name)
    url = f"https://pokeapi.co/api/v2/pokemon/{name_en}"
    try:
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            species = data["species"]["name"]
            print(f"✅ PokéAPI判定: {ocr_name} → {species}")
            nick_cache[ocr_name] = species
            safe_save(NICK_MAP, nick_cache)

            # HOMEデータに反映
            poke_data = get_pokemon_data(species)
            if poke_data:
                home_data[species] = poke_data
                safe_save_json(HOME_JSON, home_data)
                print(f"💾 HOMEデータ更新完了: {species}")
            return species
    except Exception:
        pass

    # 3️⃣ 手動入力補完
    print(f"⚠️ {ocr_name} の正式名を特定できません。")
    manual = input("👉 このポケモンの正式名を入力してください（例: カイリュー）: ").strip()
    if manual:
        nick_cache[ocr_name] = manual
        safe_save(NICK_MAP, nick_cache)
        print(f"📝 登録完了: {ocr_name} → {manual}")

        # PokéAPIから自動取得してHOME更新
        poke_data = get_pokemon_data(manual)
        if poke_data:
            home_data[manual] = poke_data
            safe_save_json(HOME_JSON, home_data)
            print(f"💾 PokéAPIから {manual} の情報をHOMEデータに追加しました。")
        return manual
    else:
        print("❌ 入力がなかったため 'unknown' として扱います。")
        return "unknown"