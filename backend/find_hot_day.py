import datetime, sys
sys.path.insert(0, ".")
from services import open_data_service as od

lat, lon = 31.5667, 74.3097          # Anarkali
rows = []
d = datetime.date(2026, 5, 1)
while d <= datetime.date(2026, 6, 30):
    try:
        t = od.fetch_weather(lat, lon, d)["hourly"]["temperature_2m"][14]   # 14:00
        if t is not None:
            rows.append((t, d))
    except Exception as e:
        print(d, "failed:", e)
    d += datetime.timedelta(days=1)

for t, d in sorted(rows, reverse=True)[:5]:
    print(d, t)