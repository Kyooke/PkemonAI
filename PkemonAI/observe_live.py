# observe_live.py
# ============================================
# ⚡ リアルタイム観戦学習AI（改良版）
# - OCR精度向上＋HPバー解析対応
# ============================================

import os
import time
import json
import re
from datetime import datetime
from collections import defaultdict

import cv2
import numpy as np
import pytesseract
import mss

# ======= Tesseract OCR設定 =======
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

OCR_CONFIG_JP = "--oem 3 --psm 7 -l jpn"

# ======= 出力ディレクトリ =======
DATA_DIR = "data"
LIVE_JSON = os.path.join(DATA_DIR, "observe_live.json")
STATS_JSON = os.path.join(DATA_DIR, "observed_stats.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ======= キャプチャ領域（フルHD前提） =======
REGIONS = {
    "my_name": {"left": 130, "top": 870, "width": 340, "height": 90},
    "my_hp":   {"left": 240, "top": 910, "width": 200, "height": 40},
    "opp_name":{"left":1420, "top": 80, "width": 360, "height": 70},
    "opp_hp":  {"left":1500, "top":130, "width": 280, "height": 30},
    # 技名欄をより正確に
    "move":    {"left": 1180, "top": 660, "width": 420, "height": 140},
}

CAP_INTERVAL = 1.0  # 1秒ごとにキャプチャ
STATS_UPDATE_EVERY = 30  # 約30秒ごとに統計更新


# ======= OCRユーティリティ =======
def pil_to_cv(img):
    arr = np.array(img)
    if arr.shape[2] == 4:
        arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
    return arr

def ocr_for_region(img):
    """コントラスト補強＋適応的二値化でOCR"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.convertScaleAbs(gray, alpha=1.6, beta=10)
    gray = cv2.medianBlur(gray, 3)
    th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 11, 2)
    text = pytesseract.image_to_string(th, config=OCR_CONFIG_JP)
    return text.strip()


# ======= HPバー解析 =======
def extract_hp_by_bar(img):
    """HPバーの緑部分の割合でHP%を推定"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([35, 80, 80])
    upper = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    ratio = np.sum(mask > 0) / mask.size
    return round(min(100, max(0, ratio * 200)), 1)  # UI補正あり


# ======= 統計更新 =======
def update_stats(samples):
    stats = defaultdict(lambda: {"count": 0, "sum_my_hp": 0.0, "sum_opp_hp": 0.0})
    for s in samples:
        move = (s.get("move_text") or "").strip()
        if not move:
            continue
        st = stats[move]
        st["count"] += 1
        st["sum_my_hp"] += s.get("my_hp", 0)
        st["sum_opp_hp"] += s.get("opp_hp", 0)

    merged = {}
    for move, v in stats.items():
        c = v["count"]
        merged[move] = {
            "count": c,
            "avg_my_hp": round(v["sum_my_hp"]/c, 2),
            "avg_opp_hp": round(v["sum_opp_hp"]/c, 2)
        }

    if os.path.exists(STATS_JSON):
        try:
            with open(STATS_JSON, "r", encoding="utf-8") as f:
                prev = json.load(f)
        except:
            prev = {}
    else:
        prev = {}

    for k, v in merged.items():
        if k in prev:
            pc = prev[k]["count"]
            nc = pc + v["count"]
            prev[k]["avg_my_hp"] = round(
                (prev[k]["avg_my_hp"]*pc + v["avg_my_hp"]*v["count"]) / nc, 2)
            prev[k]["avg_opp_hp"] = round(
                (prev[k]["avg_opp_hp"]*pc + v["avg_opp_hp"]*v["count"]) / nc, 2)
            prev[k]["count"] = nc
        else:
            prev[k] = v

    with open(STATS_JSON, "w", encoding="utf-8") as f:
        json.dump(prev, f, ensure_ascii=False, indent=2)
    print(f"📈 統計更新: {len(samples)}件 → {STATS_JSON}")


# ======= メインループ =======
def run_live_observer(duration_minutes=None):
    print("=== 🎥 リアルタイム観戦学習モード ===")
    print("Ctrl+C で終了します。")

    sct = mss.mss()
    samples = []
    frame_count = 0
    max_frames = None
    if duration_minutes:
        max_frames = int(duration_minutes * 60 / CAP_INTERVAL)

    try:
        while True:
            frame_count += 1
            timestamp = datetime.now().isoformat(timespec="seconds")
            sample = {"time": timestamp}

            # 領域ごとにキャプチャしてOCR
            for key, reg in REGIONS.items():
                try:
                    s = sct.grab(reg)
                    img = pil_to_cv(s)
                except Exception:
                    continue

                if key == "move":
                    txt = ocr_for_region(img)
                    sample["move_text"] = txt.splitlines()[0].strip() if txt else ""
                elif key == "my_hp":
                    sample["my_hp"] = extract_hp_by_bar(img)
                elif key == "opp_hp":
                    sample["opp_hp"] = extract_hp_by_bar(img)

            samples.append(sample)

            # 一定間隔で統計更新
            if frame_count % STATS_UPDATE_EVERY == 0:
                update_stats(samples)
                samples = []

            if max_frames and frame_count >= max_frames:
                print("⏱ 指定時間終了。観戦停止。")
                break

            time.sleep(CAP_INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 中断されました。")

    finally:
        if samples:
            update_stats(samples)
        print("✅ 観戦学習を終了しました。")


# ======= 実行入口 =======
if __name__ == "__main__":
    run_live_observer(duration_minutes=None)