# input_home_data.py

# =========================================

# PokéAPI連携 + 日本語対応 + AI補完版

# =========================================

import os
import json
import random
import requests

DATA_DIR = "data"
HOME_JSON = os.path.join(DATA_DIR, "home_data.json")

def safe_load_json(path):
if not os.path.exists(path):
return {}
try:
with open(path, "r", encoding="utf-8") as f:
return json.load(f)
except json.JSONDecodeError:
print(f"⚠️ {path} が空または壊れているため初期化します")
return {}

def safe_save_json(path, data):
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
json.dump(data, f, ensure_ascii=False, indent=2)

def jp_to_en(name_ja):
name_map = {
"ドドゲザン": "kingambit",
"サーフゴー": "gholdengo",
"カイリュー": "dragonite",
"テツノツツミ": "iron-bundle",
"モロバレル": "amoonguss",
}
return name_map.get(name_ja, name_ja.lower())

def generate_random_item(poke_type):
items = ["こだわりスカーフ", "いのちのたま", "きあいのタスキ"]
return random.choice(items)

def generate_random_nature():
natures = ["ようき", "いじっぱり", "おくびょう"]
return random.choice(natures)

def generate_random_evs():
return {"HP": 0, "攻撃": 252, "防御": 0, "特攻": 0, "特防": 4, "素早さ": 252}

def get_pokemon_data(name_ja):
name_en = jp_to_en(name_ja)
url = f"https://pokeapi.co/api/v2/pokemon/{name_en}"
try:
res = requests.get(url)
res.raise_for_status()
data = res.json()
except Exception:
print(f"❌ PokéAPI取得失敗: {name_ja}")
return None

```
types = [t["type"]["name"] for t in data["types"]]
stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
moves = [m["move"]["name"] for m in data["moves"]]
return {
    "types": types,
    "stats": stats,
    "moves": random.sample(moves, min(4, len(moves))),
    "item": generate_random_item(types[0]),
    "nature": generate_random_nature(),
    "evs": generate_random_evs(),
}
```

def update_home_data(pokemon_names):
home_data = safe_load_json(HOME_JSON)
for name in pokemon_names:
data = get_pokemon_data(name)
if data:
home_data[name] = data
safe_save_json(HOME_JSON, home_data)
print(f"✅ HOMEデータを保存しました ({len(home_data)}件)")
