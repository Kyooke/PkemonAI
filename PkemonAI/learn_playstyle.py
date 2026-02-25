# learn_playstyle.py
# ============================================
# 🧠 プレイング改善AI（観戦統計＋自己対戦ログ学習＋戦闘AI反映）
# ============================================

import os
import json
from datetime import datetime
from collections import defaultdict

# ======== 定数とディレクトリ設定 ========
DATA_DIR = "data"
MEMORY_PATH = os.path.join(DATA_DIR, "playstyle_memory.json")
OBSERVED_PATH = os.path.join(DATA_DIR, "observed_stats.json")
BATTLE_LOG_DIR = os.path.join(DATA_DIR, "battle_logs")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BATTLE_LOG_DIR, exist_ok=True)


# ======== JSON安全読み書き ========
def safe_load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        print(f"⚠ JSON読込失敗: {path}")
        return {}

def safe_save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠ JSON保存失敗: {e}")


# ======== 観戦学習データ統合 ========
def integrate_observed_stats(memory):
    observed = safe_load_json(OBSERVED_PATH)
    if not observed:
        print("⚠ 観戦統計が見つかりません。まず observe_live.py を実行してください。")
        return memory

    for move, info in observed.items():
        c = info.get("count", 1)
        my_hp = info.get("avg_my_hp", 0)
        opp_hp = info.get("avg_opp_hp", 0)

        # 有効性スコア = 「相手HP減少」＋「自分HP維持」
        success = max(0.0, (100 - opp_hp) * 0.7 + my_hp * 0.3)

        if move not in memory:
            memory[move] = {
                "used": c,
                "success": success * c,
                "avg_success": round(success, 2),
                "last_update": datetime.now().isoformat(),
                "source": "observe"
            }
        else:
            prev = memory[move]
            total_used = prev["used"] + c
            new_avg = ((prev["avg_success"] * prev["used"]) + (success * c)) / total_used
            memory[move].update({
                "used": total_used,
                "success": prev["success"] + success * c,
                "avg_success": round(new_avg, 2),
                "last_update": datetime.now().isoformat()
            })

    print(f"📈 観戦データを統合しました ({len(observed)} moves)")
    return memory


# ======== 自己対戦ログ統合 ========
def integrate_battle_logs(memory):
    for filename in os.listdir(BATTLE_LOG_DIR):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(BATTLE_LOG_DIR, filename)
        log = safe_load_json(path)
        if not log:
            continue

        for action in log.get("actions", []):
            move = action.get("move")
            result = action.get("result", 0.0)
            if not move:
                continue

            memory.setdefault(move, {"used": 0, "success": 0.0, "avg_success": 0.0, "source": "battle"})
            mem = memory[move]
            mem["used"] += 1
            mem["success"] += result
            mem["avg_success"] = round(mem["success"] / mem["used"], 2)
            mem["last_update"] = datetime.now().isoformat()

    print("🗂 自己対戦ログを統合しました。")
    return memory


# ======== 行動スコアの参照（戦闘AI向け） ========
def get_move_priority(memory, move_name):
    """学習済み行動傾向から技優先度を取得"""
    if move_name not in memory:
        return 1.0
    data = memory[move_name]
    score = data["avg_success"]
    used = data["used"]
    weight = 1 + min(0.5, used / 1000)
    return round(score * weight, 2)


# ======== メモリ読込関数（戦闘AIが使用） ========
def load_playstyle_memory():
    """AIが現在の行動傾向データを読み込む"""
    if not os.path.exists(MEMORY_PATH):
        print("⚠ playstyle_memory.json が存在しません。新規作成します。")
        return {}
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"📘 行動傾向メモリを読み込みました ({len(data)} moves)")
        return data
    except Exception as e:
        print(f"⚠ メモリ読込エラー: {e}")
        return {}


# ======== メイン学習統合関数 ========
def run_learning():
    """観戦データ＋自己対戦ログを統合して学習結果を保存"""
    print("=== 🧠 プレイング学習開始 ===")
    memory = safe_load_json(MEMORY_PATH)

    memory = integrate_observed_stats(memory)
    memory = integrate_battle_logs(memory)

    safe_save_json(MEMORY_PATH, memory)
    print(f"✅ 学習完了: 保存先 {MEMORY_PATH} ({len(memory)} entries)")


# ======== 実行部 ========
if __name__ == "__main__":
    run_learning()