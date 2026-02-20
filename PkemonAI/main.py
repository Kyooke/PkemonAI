# main.py
from input_home_data import input_home_data
from build_team import build_team
from select_team import select_team
from realtime_ai import battle_ai

def main():
    print("=== Pokémon AI System ===")
    print("1. HOMEデータ入力")
    print("2. 構築生成")
    print("3. 選出")
    print("4. 行動判断")
    print("5. 終了")

    while True:
        choice = input("番号を選んでください: ")

        if choice == "1":
            input_home_data()
        elif choice == "2":
            build_team()
        elif choice == "3":
            select_team()
        elif choice == "4":
            battle_ai()
        elif choice == "5":
            print("終了します。")
            break
        else:
            print("1～5の数字を入力してください。")

if __name__ == "__main__":
    main()
