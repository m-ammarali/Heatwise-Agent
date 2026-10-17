"""Run this BEFORE you present:  python check_setup.py
Verifies every data source HeatWise needs from this machine's network."""
from __future__ import annotations

import datetime
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from services import open_data_service as od, qwen_service  # noqa: E402

LAT, LON = 31.5889, 74.3147   # Lahore Fort
ok = True


def step(name, fn):
    global ok
    try:
        detail = fn()
        print(f"  [ OK ] {name}: {detail}")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"  [FAIL] {name}: {exc}")


print(f"Provider setting: DATA_PROVIDER={os.getenv('DATA_PROVIDER', 'open_data')}")
today = datetime.date.today()
step("Open-Meteo weather (today)", lambda: (
    lambda w: f"{len(w['hourly']['time'])} hourly points, elevation {w.get('elevation_m')} m"
)(od.fetch_weather(LAT, LON, today)))
step("Open-Meteo weather (tomorrow)", lambda: (
    lambda w: f"{len(w['hourly']['time'])} hourly points"
)(od.fetch_weather(LAT, LON, today + datetime.timedelta(days=1))))
step("OpenStreetMap / Overpass land cover", lambda: (
    lambda l: f"impervious {l['impervious_pct']}%, vegetation {l['tree_canopy_pct']}%, "
              f"confidence {l['confidence']} ({l['osm_feature_count']} features)"
)(od.fetch_landcover(LAT, LON)))
if qwen_service.is_configured():
    step("Qwen (Alibaba Cloud Model Studio)", lambda: (qwen_service.ask("Reply with the single word: ready", 10) or
                                                       (_ for _ in ()).throw(RuntimeError("no reply - check key/region/model name"))))
else:
    print("  [ -- ] Qwen: DASHSCOPE_API_KEY not set (optional; rule-based text will be used)")
print("\nAll required sources reachable." if ok else
      "\nSome sources failed. HeatWise will still run: it falls back to cached data, then Demo Mode.")
sys.exit(0 if ok else 1)
