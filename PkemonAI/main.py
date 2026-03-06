# ============================================
# 🏆 Pokemon AI Main Controller - Final Integrated Edition
# 構築 / 学習 / 観戦 / 実戦 / 最適化 の完全統合メニュー
# ============================================

import os
import time
import build_team as team_builder
from assist_and_learn import assist_and_learn_cycle
from learn_playstyle import run_learning
from realtime_ai import BattleAI
from input_home_data import get_pokemon_data
from observe_live import observe_live_stream
from ev_build_optimizer import optimize_build

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
    print("2️⃣  構築生成（主軸＋役割補完AI）")
    print("3️⃣  バトルAIモード（リアルタイム）")
    print("4️⃣  観戦学習モード（他人の試合分析）")
    print("5️⃣  プレイング学習（観戦＋自己対戦）")
    print("6️⃣  Assist & Learn（相手記録＋分析）")
    print("7️⃣  構築進化AI（戦績から最適化）")  # ← 追加
    print("8️⃣  終了")
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
    if not data:
        print(f"⚠️ {name} のデータ取得に失敗しました。")
        return
    print(f"✅ {name} のデータを登録しました。")
    print(data)

def run_build_team():
    """構築生成"""
    print("\n=== 🧱 構築生成AI 起動 ===")
    team_builder.build_team()

def run_realtime_ai():
    """実戦AI"""
    print("\n=== ⚔️ バトルAIモード起動 ===")
    ai = BattleAI()
    # OCRまたは手入力で相手チームを設定
    opponents = input("相手ポケモンをカンマ区切りで入力（例: カイリュー,テツノツツミ）> ").split(",")
    opponents = [x.strip() for x in opponents if x.strip()]
    ai.simulate_battle(opponents)

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

def run_optimizer():
    """構築進化AI"""
    print("\n=== 🧬 構築進化AI（EV・持ち物・構成最適化） ===")
    mode = input("1: 分析のみ / 2: 最適化して保存 > ").strip()
    if mode == "2":
        optimize_build(apply_changes=True)
    else:
        optimize_build(apply_changes=False)

# --------------------------------------------
# メインループ
# --------------------------------------------
def main():
    while True:
        show_menu()
        choice = input("選択番号を入力してください > ").strip()

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
            run_optimizer()
        elif choice == "8":
            print("👋 終了します。")
            break
        else:
            print("⚠️ 無効な入力です。1〜8を選択してください。")

        print("\n--- 戻るにはEnterキーを押してください ---")
        input()

# --------------------------------------------
# 実行
# --------------------------------------------
if __name__ == "__main__":
    main()