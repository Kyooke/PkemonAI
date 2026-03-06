# ============================================
# 👀 observe_live.py
# 他人の対戦から技選択傾向を観察し、AI学習データに反映
# ============================================

import os
import json
import random
import time
from datetime import datetime
from learn_playstyle import run_learning

DATA_DIR = "data"
OBSERVED_PATH = os.path.join(DATA_DIR, "observed_stats.json")
BATTLE_LOG_DIR = os.path.join(DATA_DIR, "battle_logs")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BATTLE_LOG_DIR, exist_ok=True)


def safe_load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def safe_save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def observe_live_stream():
    """
    観戦モード：
    ランダムな試合データを生成し、他人の技使用傾向を保存。
    その後、自動的にプレイング学習(run_learning)を呼び出す。
    """
    print("\n=== 👀 観戦学習モード開始 ===")
    moves = ["ムーンフォース", "かみくだく", "ハイドロポンプ", "シャドーボール", "ドレインパンチ", "10まんボルト", "じしん"]

    observed = {}
    for _ in range(random.randint(8, 12)):  # 試合内のランダム行動を生成
        move = random.choice(moves)
        observed.setdefault(move, {"count": 0, "avg_my_hp": 100, "avg_opp_hp": 100})
        observed[move]["count"] += 1
        observed[move]["avg_my_hp"] = random.randint(40, 100)
        observed[move]["avg_opp_hp"] = random.randint(0, 100)

    # 観戦データ保存
    safe_save_json(OBSERVED_PATH, observed)
    print(f"📁 観戦データを保存しました → {OBSERVED_PATH}")

    # 自動学習統合
    print("🧠 観戦データをプレイング学習に統合中...")
    run_learning()
    print("✅ 観戦学習モード完了。")

    # 観戦後に簡易レポートを表示
    print("\n=== 📊 観戦まとめ ===")
    for move, info in observed.items():
        print(f"{move}: 使用回数 {info['count']} 平均自HP {info['avg_my_hp']} / 相手HP {info['avg_opp_hp']}")