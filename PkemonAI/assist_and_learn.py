# assist_and_learn.py
# ============================================
# 対戦支援＆試合後学習統合スクリプト
# - ターンごとにAI助言を表示（プレイヤー操作で実行）
# - 試合ログを保存し、learn_playstyle.run_learning() を自動実行
# ============================================

import os
import time
import json
import random
from datetime import datetime

# --- 既存モジュール（あなたのプロジェクトにある前提） ---
from learn_playstyle import load_playstyle_memory, get_move_priority, run_learning
from identify_opponent import resolve_opponent_name
from input_home_data import safe_load_json, safe_save_json, get_pokemon_data, jp_to_en
from type_chart import TYPE_CHART

# --- OCR / 画面キャプチャは既存実装を参照しています ---
# この補助スクリプトは主に「助言表示」と「ログ/学習の自動化」を担います。
# 画面読み取りは既にある realtime_ai / observe_live の関数を使ってください。
# ここでは、簡易化のために "get_screen_state" の代わりに
# あなたが手動で入力する or 既存OCR関数を呼ぶ箇所を用意しています。

DATA_DIR = "data"
BATTLE_LOG_DIR = os.path.join(DATA_DIR, "battle_logs")
SUGGESTIONS_JSON = os.path.join(DATA_DIR, "suggestions.json")
os.makedirs(BATTLE_LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------
# ユーティリティ
# -------------------------
def safe_load(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def safe_save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -------------------------
# タイプ有利計算ユーティリティ
# -------------------------
def effectiveness_of_move(move_type, defender_types):
    e = 1.0
    for d in defender_types:
        e *= TYPE_CHART.get(move_type, {}).get(d, 1.0)
    return e


# -------------------------
# 推奨ロジック（助言のコア）
# -------------------------
def recommend_actions(my_active, my_hp, opp_active, opp_types, home_data, team_names):
    """
    戦略：
     - 技候補を提示（get_move_priority + タイプ効果）
     - 交代推奨 or 居座り or 交代技優先 を出す
    戻り値:
     {
       "best_move": str,
       "move_scores": [(move,score,reason),...],
       "switch_recommendation": ("stay"/"switch"/"u_turn"/"sacrifice", target, reason)
     }
    """
    res = {"best_move": None, "move_scores": [], "switch_recommendation": None}

    # 簡易home_data 整形
    hd = home_data
    my_info = hd.get(my_active, {})
    my_moves = list(my_info.get("moves", {}).keys()) if isinstance(my_info.get("moves", {}), dict) else []
    my_types = my_info.get("types", [])

    # 評価：タイプ効果 × 学習優先度 × 基礎威力係数
    for mv in my_moves:
        # move_type を home_data（もしくは既知テーブル）から推定
        minfo = hd.get(mv, {}) or {}
        move_type = min(minfo.get("type","ノーマル"), key=lambda x: len(x)) if isinstance(min if False else move_type_scrub(mv, hd), str) else move_type_scrub(mv, hd)
        # fallback: ノーマル
        if not move_type:
            move_type = "ノーマル"
        eff = effectiveness_of_move(move_type, opp_types)
        learned = get_move_priority(load_playstyle_memory(), mv)
        base_power = 80 if eff >= 1 else 60
        score = base_power * eff * (1.0 + learned/100.0)
        reason = f"eff={eff:.2f}, learned={learned}"
        res["move_scores"].append((mv, score, reason))

    # sort moves
    res["move_scores"].sort(key=lambda x: x[1], reverse=True)
    res["best_move"] = res["move_scores"][0][0] if res["move_scores"] else None

    # 交代/居座り判定（簡易）
    # opponent -> my effectiveness comparison
    def eff_vs(typesA, typesB):
        m = 1.0
        for a in typesA:
            for b in typesB:
                m *= TYPE_CHART.get(a, {}).get(b, 1.0)
        return m

    my_off = eff_vs(my_types, opp_types)
    opp_off = eff_vs(opp_types, my_types)
    net = my_off / (opp_off + 0.01)
    is_disadv = net < 0.8
    # check for u-turn-like moves
    has_u_turn = any(x in my_moves for x in ["とんぼがえり", "ボルトチェンジ", "クイックターン"])
    low_hp = my_hp < 25

    teammates = [t for t in team_names if t != my_active]
    best_switch = None
    if teammates:
        best_switch = sorted([(t, len(set(hd.get(t,{}).get("types",[])) & set(opp_types))) for t in teammates], key=lambda x: x[1], reverse=True)[0]

    if not is_disadv:
        res["switch_recommendation"] = ("stay", None, "有利対面のため居座り推奨")
    elif has_u_turn:
        res["switch_recommendation"] = ("u_turn", None, "交代技で撤退推奨")
    elif is_disadv and best_switch and best_switch[1] > 0 and not low_hp:
        res["switch_recommendation"] = ("switch", best_switch[0], "不利対面・交代推奨")
    elif is_disadv and low_hp:
        res["switch_recommendation"] = ("sacrifice", None, "HP低く切った方が良い")
    else:
        res["switch_recommendation"] = ("stay", None, "明確な交代理由なし")

    return res


# -------------------------
# move type scrub: try to determine move's type from home_data or fallback mapping
# -------------------------
def move_type_scrub(move_name, home_data):
    # if the move exists as a key in home_data and has type info
    minfo = home_data.get(move_name, {})
    t = min(minfo.get("type","ノーマル"), key=lambda x: len(x)) if isinstance(minfo.get("type","ノーマル"), list) else min if False else None
    # simple mapping fallback
    fallback = {
        "じしん":"ground","ドラゴンクロー":"dragon","はねやすめ":"flying","まもる":"normal",
        "でんじは":"electric","かみなり":"electric","あくのはどう":"dark"
    }
    return min(minfo.get("type","ノーマル"), key=lambda x: len(x)) if isinstance(minfo.get("type","ノーマル"), list) else fallback.get(move_name, "ノーマル")


# -------------------------
# 対戦の流れ（手動操作＋AI助言）
# -------------------------
def assist_battle_loop():
    """
    対戦の進め方（プレイヤー操作前提）
    - 初期で自分のチームを読み込み、相手のOCR取得（ここは簡易的に入力）
    - ターンごとにAI助言を表示。プレイヤーはそれを参考に手動で操作。
    - 操作完了後 Enter を押すと次ターンへ進む（AIがログを記録）
    - 試合終了後、自動で学習(run_learning)を実行
    """

    print("=== 対戦支援モード開始 ===")
    home_data = safe_load_json("data/home_data.json") or {}
    team_obj = safe_load_json("data/team.json") or []
    if isinstance(team_obj, dict) and "team" in team_obj:
        team_names = [p["name"] for p in team_obj["team"]]
    elif isinstance(team_obj, list):
        if team_obj and isinstance(team_obj[0], dict) and "name" in team_obj[0]:
            team_names = [p["name"] for p in team_obj]
        else:
            team_names = team_obj
    else:
        team_names = list(home_data.keys())[:6]

    if not team_names:
        print("❌ team.json または home_data.json にチームが見つかりません。先に構築してください。")
        return

    # 相手の名前（OCR で取ることを想定。ここでは簡易入力）
    print("相手のポケモン名（OCRで取得したものをスペース区切りで入力してください）")
    print("例: りゅうくん つつみちゃん バレル先生")
    opp_text = input("相手OCR（ニックネーム可）: ").strip()
    opp_texts = [t for t in opp_text.split() if t]

    # resolve via identify_opponent (キャッシュ・API・手動入力)
    opponent_species = [resolve_opponent_name(t) for t in opp_texts]
    print("→ 解決済み相手種:", opponent_species)

    # 状態の初期値（実際はOCRで取得するのが望ましい）
    my_active = team_names[0]
    opp_active = opponent_species[0]
    my_hp = 100.0
    opp_hp = 100.0
    turn = 1
    suggestion_history = []

    # ループ：プレイヤーが Enter 押すごとに1ターン進行（手動操作前提）
    while True:
        # リアルの画面からHP等を拾えるならここで更新する（省略可）
        try:
            # Prompt for current HPs (簡易)
            tmp_my = input(f"[Turn {turn}] あなたの {my_active} の現在HP% を入力してください（Enterで保持 {my_hp}%）: ").strip()
            if tmp_my:
                my_hp = float(tmp_my)
            tmp_opp = input(f"相手 {opp_active} の現在HP% を入力してください（Enterで保持 {opp_hp}%）: ").strip()
            if tmp_opp:
                opp_hp = float(tmp_opp)
        except Exception:
            print("入力無効。前のHP値を使用します。")

        # 助言を作成
        rec = recommend_actions(my_active, my_hp, opp_active, home_data.get(opp_active, {}).get("types", ["ノーマル"]), home_data, team_names)
        print("\n=== AI助言 ===")
        print(f"推奨技: {rec['best_move']}")
        print("技候補（上位3）:")
        for mv, sc, reason in rec["move_scores"][:3]:
            print(f" - {mv}: score={sc:.2f}  ({reason})")
        sw, tgt, reason = rec["switch_recommendation"]
        if sw == "switch" and tgt:
            print(f"交代推奨: {tgt} — 理由: {reason}")
        elif sw == "u_turn":
            print(f"交代技推奨（U-turn等） — 理由: {reason}")
        elif sw == "sacrifice":
            print(f"切り推奨（犠牲） — 理由: {reason}")
        else:
            print(f"居座り推奨 — 理由: {reason}")
        print("=================\n")

        # ログ保存（ターン単位で）
        suggestion = {
            "turn": turn,
            "time": datetime.now().isoformat(),
            "my_active": my_active,
            "opp_active": opp_active,
            "my_hp": my_hp,
            "opp_hp": opp_hp,
            "best_move": rec["best_move"],
            "move_scores": rec["move_scores"][:5],
            "switch": rec["switch_recommendation"]
        }
        suggestion_history.append(suggestion)

        # suggestions.json に追記しておく
        prev = safe_load(SUGGESTIONS_JSON) or []
        prev.append(suggestion)
        safe_save(SUGGESTIONS_JSON, prev)

        # プレイヤーが実行 -> Enter 押下で次ターン
        inp = input("実際の操作を行ってから Enter を押してください（q + Enter で試合終了）: ").strip()
        if inp.lower() == "q":
            print("試合終了指示を受け取りました。終了処理へ移行します。")
            break

        # プレイヤーが交代した場合は active を更新する簡易処理を尋ねる
        sw_input = input("交代は行いましたか？ 交代先の名前を入力（Enterで変化なし）: ").strip()
        if sw_input:
            if sw_input in team_names:
                my_active = sw_input
            else:
                # もし新しい呼び名なら追加はせず仮で扱う
                my_active = sw_input

        # 相手交代を手動で入力する場合
        opp_switch = input("相手が交代しましたか？ 交代先の正式名(またはニックネーム)を入力（Enterで変化なし）: ").strip()
        if opp_switch:
            # resolve and update opp_active
            opp_active = resolve_opponent_name(opp_switch)
            if opp_active not in home_data:
                # get_pokemon_data を使って home_data 更新しておく（identify_opponent が既にやっている場合は不要）
                pinfo = get_pokemon_data(opp_active)
                if pinfo:
                    home_data[opp_active] = pinfo
                    safe_save_json("data/home_data.json", home_data)

        turn += 1

    # 試合後：ログを battle_logs に保存
    battle_filename = f"battle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    battle_path = os.path.join(BATTLE_LOG_DIR, battle_filename)
    battle_log = {
        "time": datetime.now().isoformat(),
        "opponent": opponent_species,
        "suggestions": suggestion_history
    }
    safe_save(battle_path, battle_log)
    print(f"💾 試合ログを保存しました: {battle_path}")

    # 自動で学習実行
    print("\n=== 試合終了 — 学習を実行します（観戦データと自己ログを統合） ===")
    try:
        run_learning()
        print("✅ 学習が完了しました。次回からAIに反映されます。")
    except Exception as e:
        print("⚠ 学習処理でエラーが発生しました:", e)

    print("=== 対戦支援モード終了 ===")
    

# -------------------------
# 実行部
# -------------------------
if __name__ == "__main__":
    assist_battle_loop()