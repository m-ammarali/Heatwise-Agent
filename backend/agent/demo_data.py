"""Demo Mode: bundled illustrative scenarios (Phoenix + Lahore).

Used whenever the user has no API key, requests demo mode explicitly, or a
live FortyGuard call fails mid-flow. Values are realistic and internally
consistent (plausible for Phoenix, AZ in summer) but are NOT live API
results — every response is clearly labeled as such by the caller.
"""
from __future__ import annotations

from typing import Any

DEMO_SITES: dict[str, dict[str, Any]] = {
    "Phoenix Construction Zone": {
        "latitude": 33.4484,
        "longitude": -112.0740,
        "temperature_c": 43.5,
        "heat_index_c": 46.0,
        "relative_humidity_pct": 18.0,
        "solar_ghi": 890.0,
        "solar_dni": 780.0,
        "solar_dhi": 140.0,
        "tree_canopy_pct": 3.5,
        "impervious_pct": 82.0,
    },
    "Scottsdale Work Area": {
        "latitude": 33.4942,
        "longitude": -111.9261,
        "temperature_c": 40.1,
        "heat_index_c": 42.0,
        "relative_humidity_pct": 16.0,
        "solar_ghi": 820.0,
        "solar_dni": 720.0,
        "solar_dhi": 130.0,
        "tree_canopy_pct": 11.0,
        "impervious_pct": 68.0,
    },
    "Papago Park Delivery Hub": {
        "latitude": 33.4600,
        "longitude": -111.9470,
        "temperature_c": 36.8,
        "heat_index_c": 38.0,
        "relative_humidity_pct": 20.0,
        "solar_ghi": 650.0,
        "solar_dni": 560.0,
        "solar_dhi": 120.0,
        "tree_canopy_pct": 24.0,
        "impervious_pct": 45.0,
    },
    # Lahore, Pakistan - illustrative early-summer afternoon values (NOT live data).
    "Lahore Fort (Walled City)": {
        "latitude": 31.5889, "longitude": 74.3147,
        "temperature_c": 42.3, "heat_index_c": 45.8, "relative_humidity_pct": 32.0,
        "solar_ghi": 880.0, "solar_dni": 760.0, "solar_dhi": 150.0,
        "tree_canopy_pct": 6.0, "impervious_pct": 84.0,
    },
    "Greater Iqbal Park": {
        "latitude": 31.5920, "longitude": 74.3088,
        "temperature_c": 39.6, "heat_index_c": 42.1, "relative_humidity_pct": 34.0,
        "solar_ghi": 860.0, "solar_dni": 740.0, "solar_dhi": 150.0,
        "tree_canopy_pct": 38.0, "impervious_pct": 32.0,
    },
    "Gaddafi Stadium Area": {
        "latitude": 31.5134, "longitude": 74.3335,
        "temperature_c": 41.5, "heat_index_c": 44.6, "relative_humidity_pct": 31.0,
        "solar_ghi": 870.0, "solar_dni": 750.0, "solar_dhi": 150.0,
        "tree_canopy_pct": 14.0, "impervious_pct": 71.0,
    },
}


def demo_site_for(name: str, latitude: float, longitude: float) -> dict[str, Any]:
    """Return a demo profile. If the name matches a bundled demo site, use it;
    otherwise synthesize a plausible profile from a moderate baseline so any
    location still gets a coherent demo result.
    """
    if name in DEMO_SITES:
        return DEMO_SITES[name]

    return {
        "latitude": latitude,
        "longitude": longitude,
        "temperature_c": 34.0,
        "heat_index_c": 35.5,
        "relative_humidity_pct": 30.0,
        "solar_ghi": 550.0,
        "solar_dni": 470.0,
        "solar_dhi": 110.0,
        "tree_canopy_pct": 15.0,
        "impervious_pct": 55.0,
    }
