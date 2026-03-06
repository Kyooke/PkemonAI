# -*- coding: utf-8 -*-
# convert_home_data.py
# ==========================================
# home_data.json の技リストを詳細形式に変換するスクリプト
# ==========================================

import json
import os

DATA_PATH = "data/home_data.json"

# 技のタイプ・威力など簡易データ（必要に応じて追加可能）
MOVE_LIBRARY = {
    "sandstorm": {"type": "いわ", "power": 0, "accuracy": 0, "makes_contact": False},
    "taunt": {"type": "あく", "power": 0, "accuracy": 100, "makes_contact": False},
    "rock-tomb": {"type": "いわ", "power": 60, "accuracy": 95, "makes_contact": True},
    "poison-jab": {"type": "どく", "power": 80, "accuracy": 100, "makes_contact": True},
    "iron-head": {"type": "はがね", "power": 80, "accuracy": 100, "makes_contact": True},
    "sucker-punch": {"type": "あく", "power": 70, "accuracy": 100, "makes_contact": True},
    "protect": {"type": "ノーマル", "power": 0, "accuracy": 0, "makes_contact": False}
}

def convert():
    if not os.path.exists(DATA_PATH):
        print("❌ data/home_data.json が見つかりません。")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    converted = {}
    for name, info in data.items():
        new_info = dict(info)
        moves = info.get("moves", [])

        # ✅ リスト型なら辞書に変換
        if isinstance(moves, list):
            move_dict = {}
            for mv in moves:
                move_data = MOVE_LIBRARY.get(mv.lower(), {"type": "ノーマル", "power": 50, "accuracy": 100})
                move_dict[mv] = move_data
            new_info["moves"] = move_dict

        # ✅ 英語ability → 日本語仮変換
        abilities = info.get("abilities", [])
        if isinstance(abilities, list):
            new_info["ability"] = abilities[0]  # 最初のを代表として使う

        converted[name] = new_info

    # 上書き保存
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)
    print("✅ 変換完了！home_data.json をAI対応形式に修正しました。")

if __name__ == "__main__":
    convert()
