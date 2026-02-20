# input_home_data.py
import json
import os

def input_home_data():
    print("\n=== Pokémon HOMEデータ入力 ===")
    data = {}

    # 使用率の高いポケモンを記録（例: ランクマ上位ポケモン）
    while True:
        name = input("ポケモン名を入力（終了するには Enter）: ").strip()
        if not name:
            break
        usage = input(f"{name} の使用率（％）を入力: ").strip()
        item = input(f"{name} の持ち物を入力: ").strip()
        nature = input(f"{name} の性格を入力: ").strip()
        tera = input(f"{name} のテラスタイプを入力: ").strip()
        abilities = input(f"{name} の特性を入力: ").strip()

        data[name] = {
            "usage": usage,
            "item": item,
            "nature": nature,
            "tera": tera,
            "ability": abilities
        }

    # 保存先フォルダ（data）を作成
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", "home_data.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ データを保存しました: {path}")