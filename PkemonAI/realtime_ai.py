import json
import os

def battle_ai():
    print("\n=== 構築生成モード ===")

    path = os.path.join("data", "home_data.json")
    if not os.path.exists(path):
        print("❌ HOMEデータが見つかりません。先に1番を実行してください。")
        return

    with open(path, "r", encoding="utf-8") as f:
        home_data = json.load(f)

    # 使用率の高い順にソートして上位6体を選出
    sorted_pokemon = sorted(
        home_data.items(),
        key=lambda x: float(x[1]["usage"]) if x[1]["usage"] else 0,
        reverse=True
    )

    top6 = sorted_pokemon[:6]
    team = [p[0] for p in top6]

    print("\nあなたの構築候補:")
    for p in team:
        print(f" - {p}")

    # 保存
    os.makedirs("data", exist_ok=True)
    with open("data/team.json", "w", encoding="utf-8") as f:
        json.dump(team, f, ensure_ascii=False, indent=2)

    print("\n✅ 構築データを保存しました。")