import datetime, sys
sys.path.insert(0, ".")
from services import open_data_service as od

DATE = datetime.date(2026, 6, 10)   # year, month, day. Change this line to try other dates

CANDIDATES = {
    "Anarkali Bazaar": (31.5667, 74.3097),
    "Bagh-e-Jinnah": (31.5537, 74.3313),
    "Gaddafi Stadium": (31.5133, 74.3333),
}
for name, (lat, lon) in CANDIDATES.items():
    s = od.get_site_snapshot(lat, lon, DATE, "14:00")
    l = s["land"]
    print(f"{name:16} imperv {l['impervious_pct']:5}%  veg {l['tree_canopy_pct']:5}%  "
          f"adj {s['adjustment_c']:+.1f}C  temp {s['temperature_c']}C  conf {l['confidence']}")