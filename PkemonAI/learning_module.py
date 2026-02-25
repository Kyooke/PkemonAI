# learning_module.py
import json
import os
from datetime import datetime

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === プレイング分析 ===
def analyze_play_behavior():
    print("\n=== 自己プレイ分析モード（構築固定） ===")

    path = os.path.join("data", "battle_log.json")
    if not os.path.exists(path):
        print("❌ 対戦ログが見つかりません。")
        return None

    logs = load_json(path)
    if not logs:
        print("⚠️ ログが空です。")
        return None

    stats = {
        "攻撃しすぎ": 0,
        "引くべき時に引かない": 0,
        "読み外し": 0,
        "選出ミス": 0,
        "不適切な技選択": 0
    }

    for log in logs:
        details = log.get("details", {})
        if details.get("aggressive"): stats["攻撃しすぎ"] += 1
        if details.get("no_switch"): stats["引くべき時に引かない"] += 1
        if details.get("bad_prediction"): stats["読み外し"] += 1
        if details.get("bad_select"): stats["選出ミス"] += 1
        if details.get("bad_move_choice"): stats["不適切な技選択"] += 1

    print(f"\n📊 プレイ傾向解析: {stats}")

    # 改善方針を生成
    advice = []
    if stats["攻撃しすぎ"] > 2:
        advice.append("→ 有利対面以外では無理に攻撃せず、1ターン様子見を増やす。")
    if stats["引くべき時に引かない"] > 1:
        advice.append("→ 不利対面では即交代を優先。無理な突っ張りを減らす。")
    if stats["読み外し"] > 2:
        advice.append("→ 相手の行動パターンを3ターン単位で予測してリスクを減らす。")
    if stats["選出ミス"] > 1:
        advice.append("→ 相手構築の地面・鋼・フェアリー枠を初手選出で必ず意識する。")
    if stats["不適切な技選択"] > 1:
        advice.append("→ 技範囲を整理し、等倍でいいときは必中技を優先。")

    if not advice:
        advice.append("✅ 大きなプレイミスは検出されませんでした。構築維持でOKです。")

    print("\n🧠 改善提案:")
    for line in advice:
        print(line)

    return {"stats": stats, "advice": advice}

# === 構築調整（必要なときだけ） ===
def minimal_build_adjustment(stats):
    print("\n=== 構築微調整チェック ===")

    # プレイでは解決できない場合のみ構築を調整
    if stats["読み外し"] > 4 or stats["不適切な技選択"] > 3:
        print("⚙️ 技範囲不足のため、一部構築微調整を提案します。")
        home_path = os.path.join("data", "home_data.json")
        home_data = load_json(home_path)

        for name, info in home_data.items():
            moves = info.get("moves", {})
            if len(moves) < 4:
                moves["サブ技強化"] = 5.0
            info["moves"] = moves
            home_data[name] = info

        save_json(home_path, home_data)
        print("✅ HOMEデータを軽く調整しました。")
    else:
        print("構築変更は不要。プレイング改善で十分対応可能です。")

# === 学習エントリーポイント ===
def learn_play_improvement():
    print("\n=== プレイング改善学習開始 ===")
    result = analyze_play_behavior()
    if not result:
        print("⚠️ プレイデータなし。終了します。")
        return

    minimal_build_adjustment(result["stats"])

    # 履歴保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("data", "learning_history", f"{timestamp}.json")
    save_json(path, result)
    print(f"💾 学習結果を保存しました: {path}")