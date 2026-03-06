# -*- coding: utf-8 -*-
# update_move_data.py
# =============================================
# PokéAPI から技データを取得し、home_data.json に追記する
# =============================================

import json
import os
import time
import requests

DATA_PATH = "data/home_data.json"
API_BASE = "https://pokeapi.co/api/v2/move/"

# ポケAPIのタイプ英語→日本語対応辞書（簡易）
TYPE_MAP = {
    "normal": "ノーマル",
    "fire": "ほのお",
    "water": "みず",
    "electric": "でんき",
    "grass": "くさ",
    "ice": "こおり",
    "fighting": "かくとう",
    "poison": "どく",
    "ground": "じめん",
    "flying": "ひこう",
    "psychic": "エスパー",
    "bug": "むし",
    "rock": "いわ",
    "ghost": "ゴースト",
    "dragon": "ドラゴン",
    "dark": "あく",
    "steel": "はがね",
    "fairy": "フェアリー"
}


def load_home_data():
    if not os.path.exists(DATA_PATH):
        print("⚠️ home_data.json が見つかりません。")
        return {}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_home_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_move_info(move_name):
    """
    技英語名で PokéAPI を叩き、type/power/accuracy/category/makes_contact を整形して返す
    """
    url = API_BASE + move_name.lower().strip() + "/"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            print(f"❌ {move_name} API error: {r.status_code}")
            return None
        data = r.json()
    except Exception as e:
        print(f"❌ {move_name} request failed:", e)
        return None

    # 基本情報
    mtype_en = data.get("type", {}).get("name")
    mtype_jp = TYPE_MAP.get(mtype_en, "ノーマル")
    power = data.get("power") or 0
    acc = data.get("accuracy") or 0

    # 分類
    cat = data.get("damage_class", {}).get("name", "physical")
    category = "物理" if cat == "physical" else "特殊" if cat == "special" else "変化"

    # 接触判定
    makes_contact = False
    for eff in data.get("effect_entries", []):
        if "contact" in eff.get("short_effect", "").lower():
            makes_contact = True

    return {
        "type": mtype_jp,
        "power": power,
        "accuracy": acc,
        "category": category,
        "makes_contact": makes_contact
    }


def update_moves():
    home_data = load_home_data()
    if not home_data:
        return

    updated = False
    for poke, info in home_data.items():
        moves = info.get("moves", [])
        if isinstance(moves, dict) and moves:
            continue  # すでに辞書なら Ok

        if not moves:
            continue  # 空なら skip

        print(f"🛠 {poke} の技一覧を補完中…")
        move_dict = {}
        for mv in moves:
            # すでに辞書形式ならそのまま
            if isinstance(mv, dict):
                move_dict.update(mv)
                continue

            # API で取得
            mv_l = mv.replace(" ", "-").replace("　","-").lower()
            info = home_data.get("moves_cache", {}).get(mv_l)
            if info:
                print(f" ↳ {mv} をキャッシュから再利用")
                move_dict[mv] = info
                continue

            print(f" ↳ API取得: {mv}")
            move_info = fetch_move_info(mv_l)
            if move_info:
                move_dict[mv] = move_info
                home_data.setdefault("moves_cache", {})[mv_l] = move_info
            else:
                move_dict[mv] = {"type": "ノーマル", "power": 50, "accuracy": 100, "makes_contact": False}

            time.sleep(0.5)  # API 負荷対策

        info["moves"] = move_dict
        updated = True

    if updated:
        save_home_data(home_data)
        print("✅ home_data.json を更新しました。")
    else:
        print("⚠️ 更新不要（すでに辞書形式です。）")


if __name__ == "__main__":
    update_moves()