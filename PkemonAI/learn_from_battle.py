# learn_from_battle.py
# ============================================
# 対戦ログ学習AI：相手の技・持ち物・傾向を学習
# ============================================

import os
import json
from collections import defaultdict
from input_home_data import safe_load_json, safe_save_json


DATA_DIR = "data"
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")
LOG_JSON = os.path.join(DATA_DIR, "battle_log.json")


# --------------------------------------------
# 対戦ログ読み込み
# --------------------------------------------
def load_battle_logs():
    if not os.path.exists(LOG_JSON):
        print("⚠️ battle_log.json が見つかりません。まだバトルが行われていません。")
        return []
    with open(LOG_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------
# 学習データ更新
# --------------------------------------------
def update_opponent_knowledge(home_data, logs):
    learned = 0
    for record in logs:
        opponent_team = record.get("opponent", [])
        turns = record.get("turns", [])

        # 対戦相手ごとに集計
        for opp in opponent_team:
            if opp not in home_data:
                home_data[opp] = {
                    "types": ["不明"],
                    "stats": {},
                    "moves": {},
                    "items_seen": {},
                    "usage": 1.0
                }

            opp_data = home_data[opp]

            # 使用回数のカウント（出現率学習）
            opp_data["usage"] = opp_data.get("usage", 1.0) + 0.5

            # バトル中に観測された行動を解析
            for turn in turns:
                move = turn.get("action", "")
                if not move:
                    continue

                # 技の学習（出現回数を蓄積）
                if move not in ["stay", "switch", "use_u_turn", "sacrifice"]:
                    moves = opp_data.setdefault("moves", {})
                    moves[move] = moves.get(move, 0) + 1

                # 持ち物の仮定（簡易：交代時に "きあいのタスキ" の可能性を上げる等）
                if turn["action"] == "sacrifice":
                    items = opp_data.setdefault("items_seen", {})
                    items["きあいのタスキ"] = items.get("きあいのタスキ", 0) + 1

            learned += 1

    print(f"📊 {learned}件の対戦データを解析しました。")
    return home_data


# --------------------------------------------
# メイン処理
# --------------------------------------------
def learn_from_battles():
    print("\n=== 対戦ログ学習AI ===")
    logs = load_battle_logs()
    if not logs:
        return

    home_data = safe_load_json(HOME_JSON)
    updated = update_opponent_knowledge(home_data, logs)
    safe_save_json(HOME_JSON, updated)
    print("💾 HOMEデータに学習結果を反映しました。")


# --------------------------------------------
# 実行部
# --------------------------------------------
if __name__ == "__main__":
    learn_from_battles()
