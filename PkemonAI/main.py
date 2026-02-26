# ============================================

# 🏆 Pokemon AI Main Controller

# 統合メインメニュー（構築 / 学習 / 観戦 / 実戦）

# ============================================

import os
import time
from build_team import build_team
from assist_and_learn import assist_and_learn_cycle
from learn_playstyle import run_learning
from realtime_ai import realtime_battle_loop
from input_home_data import get_pokemon_data
from observe_live import observe_live_stream

DATA_DIR = "data"
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")

# --------------------------------------------

# メニュー表示

# --------------------------------------------

def show_menu():
print("\n==============================")
print("🎮 Pokemon Champions AI System")
print("==============================")
print("1️⃣  ポケモンHOMEデータ更新")
print("2️⃣  構築生成（相性考慮版）")
print("3️⃣  戦闘AIモード（リアルタイム）")
print("4️⃣  観戦モード（他人の試合学習）")
print("5️⃣  プレイング学習モード（観戦＋自己対戦）")
print("6️⃣  Assist & Learnモード（分析＋相手記録）")
print("7️⃣  終了")
print("==============================")

# --------------------------------------------

# 各モード呼び出し

# --------------------------------------------

def run_home_update():
"""HOMEデータ更新"""
print("\n=== 🏠 ポケモンHOMEデータ更新 ===")
name = input("追加するポケモン名を入力してください（例：カイリュー）> ").strip()
if not name:
print("キャンセルしました。")
return
data = get_pokemon_data(name)
print(f"✅ {name} のデータを登録しました。")
print(data)

def run_build_team():
"""構築生成"""
print("\n=== 🧱 構築生成AI 起動 ===")
build_team()

def run_realtime_ai():
"""実戦AI"""
print("\n=== ⚔️ バトルAIモード起動 ===")
realtime_battle_loop()

def run_observe():
"""観戦学習"""
print("\n=== 👀 観戦学習モード起動 ===")
observe_live_stream()

def run_playstyle_learning():
"""プレイング学習"""
print("\n=== 🧠 プレイング学習モード起動 ===")
run_learning()

def run_assist_and_learn():
"""Assist & Learn"""
print("\n=== 🎮 Assist & Learnモード起動 ===")
assist_and_learn_cycle()

# --------------------------------------------

# メインループ

# --------------------------------------------

def main():
while True:
show_menu()
choice = input("選択番号を入力してください > ").strip()

```
    if choice == "1":
        run_home_update()
    elif choice == "2":
        run_build_team()
    elif choice == "3":
        run_realtime_ai()
    elif choice == "4":
        run_observe()
    elif choice == "5":
        run_playstyle_learning()
    elif choice == "6":
        run_assist_and_learn()
    elif choice == "7":
        print("👋 終了します。")
        break
    else:
        print("⚠️ 無効な入力です。1〜7を選択してください。")

    print("\n--- 戻るにはEnterキーを押してください ---")
    input()
```

# --------------------------------------------

# 実行

# --------------------------------------------

if **name** == "**main**":
main()
