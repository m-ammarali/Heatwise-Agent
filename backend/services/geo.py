"""Small geo helpers (square_polygon_aoi is only used by the optional FortyGuard provider).

HeatWise's `create_heatmap` calls (a FortyGuard polygon-AOI endpoint) need a
`polygon_aoi` GeoJSON FeatureCollection, but HeatWise's product concept is
point-based work SITES, not property boundaries. Following the same pattern
the FortyGuard quickstart's own parcel notebooks use (buffer a boundary, then
area-weight the tiles), we build a small square buffer polygon around each
site's lat/lon so we can get a real, tile-averaged temperature for that site
instead of guessing or hardcoding one.
"""
from __future__ import annotations

import math

# Half-width buffer around a site's point, in meters. Matches the official
# quickstart's own parcel-analysis pattern (`BUFFER_M = 500` in
# notebooks/use_cases/parcel_site_due_diligence.ipynb), whose own docs note:
# "a parcel-only AOI would return one to four tiles, which is not a map. The
# buffer exists because..." A too-small AOI (e.g. ~300m box) can round down
# to zero tiles at granularity=60 depending on grid alignment — confirmed in
# practice (n_cells=0, empty map_data.features) at the previous 150m default.
DEFAULT_HALF_WIDTH_M = 500.0


def square_polygon_aoi(latitude: float, longitude: float, half_width_m: float = DEFAULT_HALF_WIDTH_M) -> dict:
    """Build a GeoJSON FeatureCollection polygon centered on (lat, lon).

    Matches the exact shape FortyGuard's `create_heatmap(polygon_aoi=...)`
    expects, per fortyguard/samples.py in the official quickstart repo:
    a FeatureCollection > Feature > Polygon, coordinates as [lon, lat].
    """
    lat_rad = math.radians(latitude)
    # Meters-per-degree approximations, adjusted for latitude.
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(lat_rad) or 1.0

    d_lat = half_width_m / m_per_deg_lat
    d_lon = half_width_m / m_per_deg_lon

    min_lon, max_lon = longitude - d_lon, longitude + d_lon
    min_lat, max_lat = latitude - d_lat, latitude + d_lat

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [min_lon, min_lat],
                        [max_lon, min_lat],
                        [max_lon, max_lat],
                        [min_lon, max_lat],
                        [min_lon, min_lat],
                    ]],
                },
            }
        ],
    }


def celsius_to_fahrenheit(c: float) -> float:
    return c * 9.0 / 5.0 + 32.0