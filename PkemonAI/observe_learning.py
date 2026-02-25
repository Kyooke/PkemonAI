# observe_learning.py
# ============================================
# 📺 他人のバトル観戦から行動を学習するモジュール
# - 対戦映像をOCR/画像解析で解析し行動傾向を記録
# ============================================

import os
import cv2
import pytesseract
import json
import numpy as np
from datetime import datetime

# Tesseract設定
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
OCR_CONFIG = "--oem 3 --psm 7 -l jpn"

DATA_DIR = "data"
OBSERVE_JSON = os.path.join(DATA_DIR, "observe_memory.json")
os.makedirs(DATA_DIR, exist_ok=True)

# 対戦映像のキャプチャ（動画ファイル）
def analyze_video(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    interval = int(fps * 2)  # 2秒ごとに1フレーム解析
    frame_count = 0

    results = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        if frame_count % interval != 0:
            continue

        # ---- 領域定義（雷撃画面を基準に）----
        # 自分技選択欄
        move_region = frame[640:840, 1170:1630]
        # 自分のHP
        my_hp_region = frame[910:950, 240:440]
        # 相手HP
        opp_hp_region = frame[130:160, 1500:1780]
        # ポケモン名
        my_name_region = frame[870:930, 130:470]
        opp_name_region = frame[80:150, 1420:1780]

        def text_from(img):
            return pytesseract.image_to_string(img, config=OCR_CONFIG).strip()

        my_name = text_from(my_name_region)
        opp_name = text_from(opp_name_region)
        move_text = text_from(move_region)
        my_hp = text_from(my_hp_region)
        opp_hp = text_from(opp_hp_region)

        results.append({
            "frame": frame_count,
            "my_name": my_name,
            "opp_name": opp_name,
            "move": move_text,
            "my_hp_text": my_hp,
            "opp_hp_text": opp_hp
        })

    cap.release()
    cv2.destroyAllWindows()
    print(f"✅ 映像解析完了: {len(results)} サンプル")

    # 保存
    with open(OBSERVE_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"💾 学習データ保存完了 → {OBSERVE_JSON}")


# 統計的に行動傾向を学習
def learn_from_observation():
    if not os.path.exists(OBSERVE_JSON):
        print("❌ 観戦データがありません。先に映像解析を実行してください。")
        return
    with open(OBSERVE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    memory = {}
    for d in data:
        move = d.get("move", "")
        my_hp = d.get("my_hp_text", "")
        if not move:
            continue
        hp_val = 100
        if "%" in my_hp:
            try:
                hp_val = int(my_hp.replace("%", ""))
            except:
                pass

        key = move.strip()
        if key not in memory:
            memory[key] = {"count": 0, "avg_hp": 0.0}
        memory[key]["count"] += 1
        memory[key]["avg_hp"] += hp_val

    for k in memory:
        memory[k]["avg_hp"] /= memory[k]["count"]

    with open(os.path.join(DATA_DIR, "observed_stats.json"), "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

    print("📈 行動傾向学習完了")
    for move, info in sorted(memory.items(), key=lambda x: -x[1]["count"])[:10]:
        print(f"- {move}: 使用{info['count']}回, 平均HP {info['avg_hp']:.1f}%")


if __name__ == "__main__":
    print("=== 観戦学習モード ===")
    path = input("解析する動画ファイルパスを入力してください: ").strip('"')
    analyze_video(path)
    learn_from_observation()