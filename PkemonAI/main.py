# main.py
# ============================================
# 🎮 Pokemon AI メイン統合スクリプト（観戦＋学習対応版）
# HOME更新 → 構築 → 選出 → バトル → 学習
# ============================================

import os
import sys
import time
from input_home_data import update_home_data
from build_team import build_team
from select_team import select_best_team
from realtime_ai import BattleAI
from learn_playstyle import run_learning
from observe_live import run_live_observer

MENU = """
===========================
 🎮 Pokemon AI Main Menu
===========================
1️⃣ HOMEデータを更新（input_home_data）
2️⃣ 構築を作成（build_team）
3️⃣ 最適3体を選出（select_team）
4️⃣ バトルAIを実行（BattleAI）
5️⃣ 観戦モード（observe_live）
6️⃣ 学習更新（learn_playstyle）
7️⃣ すべて自動で実行（1〜6）
0️⃣ 終了
===========================
番号を入力してください: """

def pause():
    input("\nEnterキーでメニューに戻ります...")

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


# ===== 各処理関数 =====
def run_home_update():
    print("\n=== HOMEデータ更新を開始 ===")
    update_home_data()
    print("\n✅ HOMEデータ更新が完了しました。")

def run_build_team():
    print("\n=== 構築生成を開始 ===")
    build_team()
    print("\n✅ 構築が完了しました。")

def run_select_team():
    print("\n=== 最適選出を開始 ===")
    select_best_team()
    print("\n✅ 選出が完了しました。")

def run_battle():
    print("\n=== バトルAIを開始 ===")
    ai = BattleAI()
    # 仮想相手チーム（例）
    opponent = ["カイリュー", "テツノツツミ", "モロバレル"]
    ai.simulate_battle(opponent)
    print("\n✅ バトルAIが終了しました。")

def run_observe():
    print("\n=== 観戦モード（リアルタイム学習） ===")
    print("配信画面を前面にして、Ctrl+Cで終了します。")
    run_live_observer(duration_minutes=None)
    print("\n✅ 観戦データ収集が完了しました。")

def run_learning_mode():
    print("\n=== 観戦・自己学習を統合 ===")
    run_learning()
    print("\n✅ 学習結果を更新しました。")


# ===== 自動実行モード =====
def run_all():
    print("\n=== 自動実行モード（HOME→構築→選出→バトル→学習） ===")
    run_home_update()
    run_build_team()
    run_select_team()
    run_battle()
    run_observe()
    run_learning_mode()
    print("\n✅ 一連の自動処理が完了しました。")


# ===== メインループ =====
def main():
    while True:
        clear()
        try:
            choice = input(MENU).strip()
            if choice == "1":
                clear(); run_home_update(); pause()
            elif choice == "2":
                clear(); run_build_team(); pause()
            elif choice == "3":
                clear(); run_select_team(); pause()
            elif choice == "4":
                clear(); run_battle(); pause()
            elif choice == "5":
                clear(); run_observe(); pause()
            elif choice == "6":
                clear(); run_learning_mode(); pause()
            elif choice == "7":
                clear(); run_all(); pause()
            elif choice == "0":
                print("終了します。")
                break
            else:
                print("❌ 無効な入力です。")
                time.sleep(1.5)
        except KeyboardInterrupt:
            print("\n中断されました。終了します。")
            sys.exit(0)
        except Exception as e:
            print(f"⚠️ エラー発生: {e}")
            pause()


if __name__ == "__main__":
    main()