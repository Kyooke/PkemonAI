# ============================================

# 🎮 Assist & Learn AI - 統合版

# 観戦学習 + 相手識別 + 自己分析 + 戦闘支援

# ============================================

import os
import json
import time
import random
from datetime import datetime
from collections import defaultdict
from learn_playstyle import get_move_priority
from screen_reader import capture_screen_data
from input_home_data import jp_to_en, get_pokemon_data

DATA_DIR = "data"
OPPONENT_LOG = os.path.join(DATA_DIR, "opponent_memory.json")
SELF_ANALYSIS_LOG = os.path.join(DATA_DIR, "self_analysis.json")
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")

os.makedirs(DATA_DIR, exist_ok=True)

# --------------------------------------------

# JSON 安全読み書き

# --------------------------------------------

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

# --------------------------------------------

# 🧩 相手識別 (OCR + 手動補正)

# --------------------------------------------

def identify_opponent_auto():
"""画面OCRから相手ポケモンを推測"""
screen_data = capture_screen_data()
detected = []

```
for name in screen_data.get("names", []):
    if len(name) < 2:
        continue
    detected.append(name)

if not detected:
    print("⚠️ OCRで相手を特定できません。")
    return manual_input_opponent()
print(f"🔍 検出された相手: {detected}")
return detected
```

def manual_input_opponent():
"""手動入力で相手パーティ登録"""
print("💬 相手のポケモン名を手動で入力してください（カンマ区切り）")
text = input("入力例: カイリュー, ドドゲザン, サーフゴー > ").strip()
return [x.strip() for x in text.split(",") if x.strip()]

# --------------------------------------------

# 📊 相手情報記録・学習

# --------------------------------------------

def update_opponent_memory(opponent_list):
memory = safe_load_json(OPPONENT_LOG)
for name in opponent_list:
if name not in memory:
data = get_pokemon_data(name)
memory[name] = {
"seen": 1,
"last_seen": datetime.now().isoformat(),
"types": data.get("types", []),
"stats": data.get("stats", {}),
"moves": data.get("moves", []),
}
else:
memory[name]["seen"] += 1
memory[name]["last_seen"] = datetime.now().isoformat()
safe_save_json(OPPONENT_LOG, memory)
print(f"📁 相手データを更新しました（{len(opponent_list)}体）")

# --------------------------------------------

# 🧠 自己分析モジュール（統合）

# --------------------------------------------

def analyze_self_performance():
"""勝率や構築評価の自己分析"""
data = safe_load_json(SELF_ANALYSIS_LOG)
now = datetime.now().isoformat()

```
if "history" not in data:
    data["history"] = []

recent = data["history"][-10:] if len(data["history"]) >= 10 else data["history"]
if not recent:
    print("📊 過去データがありません。初回分析をスキップします。")
    return None

win_rate = sum(1 for x in recent if x.get("result") == "win") / len(recent)
print(f"📈 直近10戦の勝率: {win_rate*100:.1f}%")

if win_rate < 0.4:
    print("⚠️ 勝率低下検出 → 構築改善を推奨")
    return "rebuild"

print("✅ 勝率は安定しています")
return "stable"
```

def record_battle_result(result: str):
"""バトル結果を記録"""
data = safe_load_json(SELF_ANALYSIS_LOG)
data.setdefault("history", [])
data["history"].append({"time": datetime.now().isoformat(), "result": result})
safe_save_json(SELF_ANALYSIS_LOG, data)
print(f"📝 バトル結果を記録: {result}")

# --------------------------------------------

# 🎮 対戦支援AI

# --------------------------------------------

def suggest_move(my_pokemon, moves, memory):
"""技候補から最適行動を提案"""
best_move = None
best_score = -999

```
for move in moves:
    score = get_move_priority(memory, move)
    if score > best_score:
        best_move = move
        best_score = score

print(f"💡 推奨行動: {best_move}（スコア: {best_score:.2f}）")
return best_move
```

# --------------------------------------------

# 🔁 総合フロー

# --------------------------------------------

def assist_and_learn_cycle():
print("=== 🎮 Assist & Learn Cycle 開始 ===")

```
# 相手特定
opponent = identify_opponent_auto()
update_opponent_memory(opponent)

# 自己分析
result = analyze_self_performance()
if result == "rebuild":
    print("🛠 自動構築モードへ移行推奨（build_team）")

print("=== ✅ Assist & Learn 完了 ===")
```

# --------------------------------------------

# 実行部

# --------------------------------------------

if **name** == "**main**":
assist_and_learn_cycle()
