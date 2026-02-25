# learning_module_advanced.py
"""
Advanced Learning Module (risk-aware, turn-simulation) for Pokémon AI.

要点:
- data/battle_log.json を読み込み、各行動のリスク評価を行う
- 簡易ターンシミュレーションで代替行動の期待値を比較
- 行動ごとの mistake_score を出し、改善アドバイスを生成
- 学習結果を data/learning_advanced/YYYYMMDD_HHMMSS.json に保存

使い方:
1) このファイルをプロジェクトに置く
2) 対戦ログを data/battle_log.json に準備
3) python learning_module_advanced.py を実行
"""

import json
import os
import random
from datetime import datetime
from copy import deepcopy
from collections import defaultdict

# ---------------------------
# ユーティリティ
# ---------------------------
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------------
# 簡易バトルモデル - 期待値/リスク計算のための近似
# （本物のダメ計を再現するのではなく、相対比較が取れることを目的とした
#  簡易モデル）
# ---------------------------
# 技カテゴリワイヤ（「物理」「特殊」「補助」）は move name によって判別しない。
# ここではログに属性があれば使う。なければランダム近似で算出。

def estimate_damage(attacker_hp_pct=1.0, defender_hp_pct=1.0, power=50, stab=1.0, effectiveness=1.0):
    """
    簡易ダメージ推定: 0-100のスケールで期待ダメージを返す
    - power: 技の仮想攻撃力
    - stab: 技のタイプ一致補正 (1.0 or 1.5)
    - effectiveness: 相性 (0, 0.5, 1, 2, ...)
    """
    base = power * stab * effectiveness
    # 攻撃側の残HPが低いと威力が下がる（経験則的に）
    factor = 0.8 + 0.4 * attacker_hp_pct  # 0.8-1.2
    return max(0.0, base * factor * (1.0 - 0.1 * (1.0 - defender_hp_pct)))

def estimate_survival_probability(my_hp_pct, incoming_expected_damage):
    """
    簡易生存確率推定: 0-1
    - incoming_expected_damage: 相手の期待ダメージ（0-100スケール）
    """
    # 単純：ダメージがHP割合を上回るほど死亡確率増
    hp_scaled = my_hp_pct * 100.0
    if incoming_expected_damage <= 0:
        return 1.0
    # logistic-ish
    diff = hp_scaled - incoming_expected_damage
    prob = 1.0 / (1.0 + pow(2.71828, -0.06 * diff))  # 調整係数
    return max(0.0, min(1.0, prob))

# ---------------------------
# ログ解析: 各行動のmistakeスコア
# ---------------------------
def score_action(record):
    """
    1行動(record)からmistake_scoreを返す。
    record: dict with keys:
      - active: 自分の行動ポケモン
      - action: "attack"/"switch"/"stay"/"item"
      - move: move name or None
      - hp_after: self hp percent (0-100)
      - opp_hp_after: opponent hp percent (0-100)
      - opponent_move: str or None
    戻り値: dict { 'score': float, 'reason': str }
    """
    # 防御側の推定インパクト（opp move）
    opp_move_power = 50
    # 簡易: 攻撃行動の期待ダメージ / 相手の期待ダメージ から優劣判断
    my_move_power = 60 if record.get("action") == "attack" else 10
    stab = 1.0
    effectiveness = 1.0
    # attacker/defender hp% を 0-1 に
    my_hp_pct = record.get("hp_before_pct", 100) / 100.0
    opp_hp_pct = record.get("opp_hp_before_pct", 100) / 100.0

    my_expected = estimate_damage(my_hp_pct, opp_hp_pct, power=my_move_power, stab=stab, effectiveness=effectiveness)
    opp_expected = estimate_damage(opp_hp_pct, my_hp_pct, power=opp_move_power)

    # survival probability if you stay and get hit
    surv_if_stay = estimate_survival_probability(my_hp_pct, opp_expected)

    score = 0.0
    reasons = []

    # 攻撃が明らかに無謀：相手の期待ダメージが高く自分の生存確率が低い場合
    if record.get("action") == "attack":
        if surv_if_stay < 0.4 and my_expected < opp_expected * 0.8:
            score += 3.0
            reasons.append("不利対面で攻撃しすぎ（危険）")
        elif my_expected < opp_expected and surv_if_stay < 0.6:
            score += 1.5
            reasons.append("攻撃対価が低い")
        else:
            score += 0.0
    elif record.get("action") == "stay":
        # 何もしなさすぎ（様子見）もミスの可能性
        if surv_if_stay < 0.5:
            score += 1.0
            reasons.append("様子見が危険（交代推奨）")
    elif record.get("action") == "switch":
        # 不要な交換（有利を捨てる）を軽減
        # ここでは交換先情報がないのでランダムに評価
        if record.get("forced_switch", False):
            score += 0.0
        else:
            # 偶発的ペナルティ小
            score += 0.2

    # opponent move が致命的だったが回避できたか（回避できたならマイナススコア＝良行動）
    if record.get("opp_hp_after", 100) <= 0 and record.get("hp_after", 0) > 0:
        # 相手を倒して生き残った→良い
        score -= 1.0
        reasons.append("決定打で生存")

    # 合計
    return {"score": round(score, 3), "reasons": reasons, "my_expected": my_expected, "opp_expected": opp_expected, "surv_if_stay": round(surv_if_stay,3)}

# ---------------------------
# 簡易シミュレーション：代替行動の期待値比較
# ---------------------------
def simulate_alternative_actions(turn_record, n_samples=20):
    """
    指定ターンで 'attack'/'switch'/'stay' の代替行動を乱数でシミュレーションして
    期待報酬（勝率推定）を返す（簡易）。
    返り値: dict { action_name: avg_score }
    """
    results = {"attack": [], "switch": [], "stay": []}

    for _ in range(n_samples):
        # ランダムな相手の反応（簡易化）
        opp_reaction_damage = random.uniform(30, 80)  # 相手の期待ダメージ
        my_hp_pct = turn_record.get("hp_before_pct", 100) / 100.0
        opp_hp_pct = turn_record.get("opp_hp_before_pct", 100) / 100.0

        # attack: 自分が与えるダメージは move power variance
        my_dmg = estimate_damage(my_hp_pct, opp_hp_pct, power=random.uniform(40,80))
        # switch: assume you lose one small turn but gain survival chance
        switch_surv = estimate_survival_probability(my_hp_pct, opp_reaction_damage * 0.8)
        # stay: accept incoming damage
        stay_surv = estimate_survival_probability(my_hp_pct, opp_reaction_damage)

        # heuristic score: 生存確率*100 + self-damage-dealt*0.5
        attack_score = estimate_survival_probability(my_hp_pct, opp_reaction_damage) * 100.0 + my_dmg * 0.5
        switch_score = switch_surv * 100.0 + (my_dmg * 0.2)
        stay_score = stay_surv * 100.0

        results["attack"].append(attack_score)
        results["switch"].append(switch_score)
        results["stay"].append(stay_score)

    summary = {k: sum(v)/len(v) if v else 0.0 for k,v in results.items()}
    return summary

# ---------------------------
# 高度解析：対戦ログ全体を精査して改善点を出す
# ---------------------------
def advanced_analyze_and_suggest(max_bad=5):
    """
    対戦ログを読み、mistake_scoreの高い行動を抽出して
    代替アクションのシミュレーションを行い、改善案を生成する。
    """
    logs = load_json(os.path.join("data", "battle_log.json"))
    if not logs:
        print("対戦ログが見つかりません。data/battle_log.json を用意してください。")
        return

    # 各行動を個別項目として抽出
    action_records = []
    for match in logs:
        match_meta = {"opponent": match.get("opponent"), "result": match.get("result")}
        for t in match.get("turns", []):
            rec = deepcopy(t)
            rec.update(match_meta)
            # 前後HPを補完（ログに無ければ hp_after を利用）
            rec["hp_before_pct"] = t.get("hp_before_pct", t.get("hp_after", 100))
            rec["opp_hp_before_pct"] = t.get("opp_hp_before_pct", t.get("opp_hp_after", 100))
            action_records.append(rec)

    # 各行動をスコアリング
    scored = []
    for rec in action_records:
        s = score_action(rec)
        rec_result = {"record": rec, "score": s["score"], "reasons": s["reasons"], "meta": {"my_expected": s["my_expected"], "opp_expected": s["opp_expected"], "surv": s["surv_if_stay"]}}
        scored.append(rec_result)

    # スコア降順（危険な行動が上）
    scored_sorted = sorted(scored, key=lambda x: x["score"], reverse=True)

    # 上位 N 件について代替アクションをシミュレーション
    top_issues = scored_sorted[:max_bad]
    suggestions = []
    for issue in top_issues:
        rec = issue["record"]
        sim = simulate_alternative_actions(rec, n_samples=50)
        best_action = max(sim.items(), key=lambda x: x[1])[0]
        suggestions.append({
            "turn": rec.get("turn"),
            "active": rec.get("active"),
            "original_action": rec.get("action"),
            "score": issue["score"],
            "reasons": issue["reasons"],
            "sim_summary": sim,
            "recommended": best_action
        })

    # 全体傾向解析（簡易）
    trend = defaultdict(int)
    for it in scored_sorted:
        for r in it["reasons"]:
            trend[r] += 1

    # 改善アドバイス生成（テンプレート）
    advice = []
    # If many "不利対面で攻撃しすぎ"
    if any("不利対面で攻撃しすぎ（危険）" in it["reasons"] for it in scored_sorted[:20]):
        advice.append("有利対面以外では攻撃を控え、交代や守るを優先してください。")
    if any("様子見が危険（交代推奨）" in it["reasons"] for it in scored_sorted[:20]):
        advice.append("HPが低いときは守る／交代を優先してください。")
    if not advice:
        advice.append("全体的な行動は大きな問題は見当たりません。")

    # 保存
    out = {
        "timestamp": datetime.now().isoformat(),
        "top_issues": suggestions,
        "trend": dict(trend),
        "advice": advice
    }
    save_path = os.path.join("data", "learning_advanced", datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
    save_json(save_path, out)

    # 表示
    print("\n=== 上位問題行動（自動サマリ） ===")
    for s in suggestions:
        print(f"Turn {s['turn']} | {s['active']} | orig={s['original_action']} -> recommend={s['recommended']} | score={s['score']}")
        print(f"  sim: {s['sim_summary']}")
        if s['reasons']:
            print(f"  reasons: {s['reasons']}")
    print("\n=== 全体アドバイス ===")
    for a in advice:
        print(" -", a)

    print(f"\n✅ 学習結果を保存しました: {save_path}")
    return out

# ---------------------------
# CLI 実行
# ---------------------------
if __name__ == "__main__":
    ensure_dir("data")
    print("Advanced Learning Module - risk-aware simulation")
    print("1) run analysis and suggestions")
    choice = input("実行しますか？ (y/n): ").strip().lower()
    if choice == "y":
        advanced_analyze_and_suggest()
    else:
        print("終了します。")