# build_team.py

# ============================================

# 構築生成AI + 記事傾向反映版

# ============================================

import os
import json
import random
from glob import glob
from type_chart import TYPE_CHART

DATA_DIR = "data"
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")
TEAM_JSON = os.path.join(DATA_DIR, "team.json")
ARTICLE_DIR = os.path.join(DATA_DIR, "articles")

def safe_load_json(path):
if not os.path.exists(path):
return {}
try:
with open(path, "r", encoding="utf-8") as f:
return json.load(f)
except:
return {}

def safe_save_json(path, data):
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
json.dump(data, f, ensure_ascii=False, indent=2)

# 記事傾向読み込み

def load_article_data():
articles = []
for path in glob(os.path.join(ARTICLE_DIR, "*.json")):
try:
with open(path, "r", encoding="utf-8") as f:
data = json.load(f)
articles.append(data)
except:
continue
return articles

def analyze_article_trends(articles):
freq = {}
for art in articles:
for p in art.get("team", []):
name = p["name"]
freq[name] = freq.get(name, 0) + 1
return sorted(freq.items(), key=lambda x: x[1], reverse=True)

# チーム構築メイン

def build_team():
print("\n=== 🧱 構築生成（記事傾向考慮） ===")
home_data = safe_load_json(HOME_JSON)
if not home_data:
print("❌ HOMEデータがありません。")
return

```
articles = load_article_data()
trend = analyze_article_trends(articles)
print(f"📈 記事人気トップ: {[t[0] for t in trend[:5]]}")

scored = []
for name, data in home_data.items():
    base = data["stats"].get("attack", 50) + data["stats"].get("speed", 50)
    trend_bonus = sum(v for n, v in trend if n == name)
    score = base / 10 + trend_bonus
    scored.append((name, score))
scored.sort(key=lambda x: x[1], reverse=True)

team = [n for n, _ in scored[:6]]
safe_save_json(TEAM_JSON, team)
print("✅ 構築完了:", team)
```
