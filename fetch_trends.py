"""يسحب الكلمات الأكثر بحثاً المرتبطة بكل مدينة من Google Trends ويكتبها في data.json"""
import json, time, random, pathlib
from datetime import datetime, timezone
from pytrends.request import TrendReq

CITIES = ["تطوان", "طنجة", "الفنيدق", "سبتة"]   # عدّل أو أضف مدن (كلمة البحث الأساسية)
PERIODS = {"24h": "now 1-d", "7d": "now 7-d"}
GEO = "MA"
LIMIT = 8
OUT = pathlib.Path("data.json")

old = {}
if OUT.exists():
    old = json.loads(OUT.read_text(encoding="utf-8"))
    if old.get("sample"):
        old = {}
old_cities = old.get("cities", {})

pt = TrendReq(hl="ar", tz=-60)

def fetch(kw, tf):
    for attempt in range(3):
        try:
            pt.build_payload([kw], timeframe=tf, geo=GEO)
            res = pt.related_queries().get(kw, {})
            top, rising = res.get("top"), res.get("rising")
            change = {}
            if rising is not None and len(rising):
                for _, r in rising.iterrows():
                    v = int(r["value"])
                    change[r["query"]] = "جديد" if v >= 5000 else f"+{v}%"
            rows = []
            if top is not None and len(top):
                for _, r in top.head(LIMIT).iterrows():
                    rows.append([r["query"], int(r["value"]), change.get(r["query"], "")])
            elif rising is not None and len(rising):
                for _, r in rising.head(LIMIT).iterrows():
                    rows.append([r["query"], 50, change.get(r["query"], "")])
            return rows
        except Exception as e:
            print("retry", kw, tf, e)
            time.sleep(30 * (attempt + 1))
    return None

cities = {}
for city in CITIES:
    cities[city] = dict(old_cities.get(city, {}))
    for key, tf in PERIODS.items():
        rows = fetch(city, tf)
        if rows:                      # لو فشل الطلب نحتفظ بآخر بيانات ناجحة
            cities[city][key] = rows
        time.sleep(random.uniform(10, 20))

OUT.write_text(json.dumps({
    "updated": datetime.now(timezone.utc).isoformat(),
    "sample": False,
    "cities": cities,
}, ensure_ascii=False, indent=1), encoding="utf-8")
