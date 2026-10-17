"""Standalone diagnostic — run directly, bypasses HeatWise entirely.

Reproduces the exact call from the official quickstart's own
notebooks/01_create_heatmap.ipynb (Manhattan polygon, a fixed historical
date, granularity=100) to get a clean baseline reading against your key.

Usage (from backend/ with your venv active):
    python diagnose_heatmap.py
"""
import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from fortyguard import FortyGuardClient

# Inlined directly from the official quickstart's fortyguard/samples.py
# (that file wasn't vendored into this project — only client.py/exceptions.py
# were copied over).
MANHATTAN_POLYGON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-74.0170, 40.7050],
                    [-74.0030, 40.7050],
                    [-74.0030, 40.7180],
                    [-74.0170, 40.7180],
                    [-74.0170, 40.7050],
                ]],
            },
        }
    ],
}

client = FortyGuardClient()

print("=" * 70)
print("TEST 1: Exact known-good notebook example")
print("        Manhattan polygon, start_date=2024-07-15 (fixed historical date)")
print("=" * 70)
try:
    response = client.create_heatmap(
        polygon_aoi=MANHATTAN_POLYGON,
        start_date="2024-07-15",
        start_time="14:00",
        filter_type=1,
        granularity=100,
        wait=True,
        verbose=True,
    )
    result = response.get("result", {})
    stats = result.get("stats_data", {})
    features = (result.get("map_data") or {}).get("features") or []
    print(f"\nactivity_id : {response.get('activity_id')}")
    print(f"stats_data  : {json.dumps(stats, indent=2)}")
    print(f"feature_count: {len(features)}")
    if features:
        print(f"sample_feature: {json.dumps(features[0], indent=2)}")
except Exception as exc:
    print(f"\nFAILED: {type(exc).__name__}: {exc}")

print()
print("=" * 70)
print("TEST 2: Same Manhattan polygon, but with TODAY's date")
print("=" * 70)
from datetime import date
today = date.today().isoformat()
try:
    response = client.create_heatmap(
        polygon_aoi=MANHATTAN_POLYGON,
        start_date=today,
        start_time="14:00",
        filter_type=1,
        granularity=100,
        wait=True,
        verbose=True,
    )
    result = response.get("result", {})
    stats = result.get("stats_data", {})
    features = (result.get("map_data") or {}).get("features") or []
    print(f"\nactivity_id : {response.get('activity_id')}")
    print(f"stats_data  : {json.dumps(stats, indent=2)}")
    print(f"feature_count: {len(features)}")
except Exception as exc:
    print(f"\nFAILED: {type(exc).__name__}: {exc}")

print()
print("=" * 70)
print("TEST 3: Same Manhattan polygon, historical date, filter_type=3 (single day)")
print("        This is the mode the use-case notebooks actually rely on.")
print("=" * 70)
try:
    response = client.create_heatmap(
        polygon_aoi=MANHATTAN_POLYGON,
        start_date="2024-07-15",
        filter_type=3,
        granularity=100,
        wait=True,
        verbose=True,
    )
    result = response.get("result", {})
    stats = result.get("stats_data", {})
    features = (result.get("map_data") or {}).get("features") or []
    print(f"\nactivity_id : {response.get('activity_id')}")
    print(f"stats_data  : {json.dumps(stats, indent=2)}")
    print(f"feature_count: {len(features)}")
    if features:
        print(f"sample_feature: {json.dumps(features[0], indent=2)}")
except Exception as exc:
    print(f"\nFAILED: {type(exc).__name__}: {exc}")