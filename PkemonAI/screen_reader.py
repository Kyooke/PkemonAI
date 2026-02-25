# screen_reader.py（OCR強化版）
# === ポケモン対戦画面をOCR + 画像解析で読み取るモジュール ===

import cv2
import numpy as np
import pytesseract
import pyautogui
import os
import time

# Tesseractパス
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# === 設定 ===
NAME_REGION = (100, 100, 250, 60)
HP_REGION = (100, 160, 300, 40)
OPP_NAME_REGION = (1000, 100, 250, 60)
OPP_HP_REGION = (1000, 160, 300, 40)

# === OCR設定（精度向上） ===
OCR_CONFIG = "--oem 3 --psm 6 -l jpn+eng"

def capture_region(region):
    """指定範囲をスクリーンキャプチャ"""
    x, y, w, h = region
    img = pyautogui.screenshot(region=(x, y, w, h))
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return frame

def extract_text(image):
    """OCRでテキストを抽出（ノイズ除去付き）"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    gray = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)[1]
    text = pytesseract.image_to_string(gray, config=OCR_CONFIG)
    text = text.strip().replace(" ", "").replace("\n", "")
    return text

def detect_hp_percent(image):
    """HPバーの緑部分の割合を推定"""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([40, 40, 40])
    upper_green = np.array([80, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    ratio = np.sum(mask > 0) / mask.size
    hp_percent = round(ratio * 100, 1)
    return hp_percent

def read_battle_screen():
    """対戦画面をリアルタイム解析して出力"""
    my_name_img = capture_region(NAME_REGION)
    my_hp_img = capture_region(HP_REGION)
    opp_name_img = capture_region(OPP_NAME_REGION)
    opp_hp_img = capture_region(OPP_HP_REGION)

    my_name = extract_text(my_name_img)
    opp_name = extract_text(opp_name_img)
    my_hp = detect_hp_percent(my_hp_img)
    opp_hp = detect_hp_percent(opp_hp_img)

    os.system('cls')
    print("=== 対戦画面解析 ===")
    print(f"あなたのポケモン: {my_name or '（認識なし）'}　HP推定: {my_hp}%")
    print(f"相手のポケモン: {opp_name or '（認識なし）'}　HP推定: {opp_hp}%")

    return {
        "my_name": my_name,
        "my_hp": my_hp,
        "opp_name": opp_name,
        "opp_hp": opp_hp
    }

if __name__ == "__main__":
    print("OCR強化版でリアルタイム解析を開始します。Ctrl + C で停止。")
    time.sleep(2)
    while True:
        read_battle_screen()
        time.sleep(1.0)