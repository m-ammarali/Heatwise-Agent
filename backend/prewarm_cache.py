"""Run this on good internet the night before:  python prewarm_cache.py
Stores weather + land cover for your demo sites so the demo survives bad venue Wi-Fi.
Edit SITES to the places you will actually present."""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from services import open_data_service as od  # noqa: E402

SITES = {
        "Anarkali Bazaar": (31.5667, 74.3097),
        "Bagh-e-Jinnah": (31.5537, 74.3313),
        "Gaddafi Stadium": (31.5133, 74.3333),
}
DAYS_AHEAD = (0, 1, 2)

today = datetime.date.today()
for name, (lat, lon) in SITES.items():
    try:
        land = od.fetch_landcover(lat, lon)
        print(f"{name}: land cover cached (impervious {land['impervious_pct']}%, vegetation {land['tree_canopy_pct']}%)")
        for d in DAYS_AHEAD:
            od.fetch_weather(lat, lon, today + datetime.timedelta(days=d))
        print(f"{name}: weather cached for {len(DAYS_AHEAD)} days")
    except Exception as exc:  # noqa: BLE001
        print(f"{name}: FAILED - {exc}")

for name, (lat, lon) in SITES.items():
    od.fetch_weather(lat, lon, datetime.date(2026, 6, 15))