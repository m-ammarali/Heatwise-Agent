"""Free, keyless data layer for HeatWise (replaces the FortyGuard API).

Sources
-------
* Open-Meteo (https://open-meteo.com, CC BY 4.0, free for non-commercial use,
  no API key): hourly air temperature, humidity, apparent temperature,
  shortwave / direct / diffuse radiation, cloud cover and site elevation.
* OpenStreetMap via the Overpass API (ODbL): buildings, roads, parking,
  parks, trees, water around each site -> impervious / vegetation / water %.

How "hyperlocal" is produced (be honest about this on stage)
-----------------------------------------------------------
Open-Meteo is a 1-11 km weather model, so two sites in the same neighbourhood
get the same base air temperature. HeatWise therefore adds a transparent,
bounded *microclimate adjustment* derived from the land cover around each
site (more pavement/buildings -> warmer, more vegetation/water -> cooler).
It is a documented estimate, NOT a sensor measurement, and every result says
so in its evidence list.
"""
from __future__ import annotations

import logging
import math
import time
from datetime import date as date_type, timedelta
from typing import Any, Optional

import requests

from services import cache

logger = logging.getLogger("heatwise.open_data")

OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
USER_AGENT = "HeatWise-Agent/2.0 (hackathon demo; open-data provider)"

HTTP_TIMEOUT_S = 25
LANDCOVER_RADIUS_M = 250.0

WEATHER_CACHE_MAX_AGE_S = 60 * 60          # fresh for 1 hour
HOURLY_VARS = (
    "temperature_2m,relative_humidity_2m,apparent_temperature,"
    "shortwave_radiation,direct_normal_irradiance,diffuse_radiation,cloud_cover"
)

# --- documented model constants (shown in the UI evidence / PDF) -----------
# Share of land cover we could not see in OSM is assumed to look like this.
UNMAPPED_IMPERVIOUS_SHARE = 0.45
UNMAPPED_VEGETATION_SHARE = 0.15
# Microclimate adjustment (deg C), relative to a "typical" neutral site.
REF_IMPERVIOUS = 0.45
REF_VEGETATION = 0.10
K_IMPERVIOUS = 3.0
K_VEGETATION = 4.0
K_WATER = 3.0
MAX_ADJUSTMENT_C = 3.5

ROAD_WIDTH_M = {
    "motorway": 14, "trunk": 12, "primary": 10, "secondary": 8, "tertiary": 7,
    "residential": 5, "unclassified": 5, "service": 4, "living_street": 5,
    "footway": 2, "path": 1.5, "cycleway": 2, "pedestrian": 4, "steps": 2, "track": 3,
}
HARD_LANDUSE = {"industrial": 0.6, "commercial": 0.6, "retail": 0.6, "construction": 0.5,
                "garages": 0.7, "railway": 0.5, "residential": 0.35}
VEG_LANDUSE = {"forest", "grass", "meadow", "orchard", "vineyard", "village_green",
               "recreation_ground", "cemetery", "farmland", "flowerbed", "greenfield"}
VEG_NATURAL = {"wood", "scrub", "grassland", "heath", "wetland", "tree_row"}
VEG_LEISURE = {"park", "garden", "golf_course", "nature_reserve", "playground"}


class OpenDataUnavailable(Exception):
    """Raised when neither live data nor a cached copy can be obtained."""


# ----------------------------------------------------------------- HTTP ----

def _http_get_json(url: str, params: dict[str, Any]) -> dict:
    resp = requests.get(url, params=params, timeout=HTTP_TIMEOUT_S,
                        headers={"User-Agent": USER_AGENT})
    if not resp.ok:
        raise OpenDataUnavailable(f"GET {url.split('/')[2]} -> HTTP {resp.status_code}")
    return resp.json()


def _http_post_overpass(query: str) -> dict:
    last: Optional[Exception] = None
    for url in OVERPASS_URLS:
        for attempt in range(2):
            try:
                resp = requests.post(url, data={"data": query}, timeout=HTTP_TIMEOUT_S + 50,
                                     headers={"User-Agent": USER_AGENT})
                if resp.ok:
                    return resp.json()
                last = OpenDataUnavailable(f"Overpass {url.split('/')[2]} -> HTTP {resp.status_code}")
            except requests.RequestException as exc:
                last = exc
            time.sleep(1.0 + attempt)
    raise OpenDataUnavailable(f"Overpass unavailable: {last}")


# ------------------------------------------------------------- weather -----

def heat_index_c(temp_c: float, rh_pct: float) -> float:
    """NWS Rothfusz heat index, returned in deg C.

    Below ~26.7 C (80 F) the regression isn't valid; return the air temperature
    (apparent temperature is then dominated by wind/humidity, not 'heat').
    """
    t_f = temp_c * 9 / 5 + 32
    rh = max(0.0, min(100.0, rh_pct))
    if t_f < 80:
        return temp_c
    hi = (-42.379 + 2.04901523 * t_f + 10.14333127 * rh - 0.22475541 * t_f * rh
          - 0.00683783 * t_f ** 2 - 0.05481717 * rh ** 2 + 0.00122874 * t_f ** 2 * rh
          + 0.00085282 * t_f * rh ** 2 - 0.00000199 * t_f ** 2 * rh ** 2)
    if rh < 13 and 80 <= t_f <= 112:
        hi -= ((13 - rh) / 4) * math.sqrt((17 - abs(t_f - 95)) / 17)
    elif rh > 85 and 80 <= t_f <= 87:
        hi += ((rh - 85) / 10) * ((87 - t_f) / 5)
    return round((max(hi, t_f) - 32) * 5 / 9, 2)


def wet_bulb_c(temp_c: float, rh_pct: float) -> float:
    """Stull (2011) wet-bulb approximation, deg C."""
    t, rh = temp_c, max(1.0, min(100.0, rh_pct))
    return round(
        t * math.atan(0.151977 * math.sqrt(rh + 8.313659))
        + math.atan(t + rh) - math.atan(rh - 1.676331)
        + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh) - 4.686035, 2)


def _weather_endpoint(analysis_date: date_type) -> str:
    today = date_type.today()
    if analysis_date > today + timedelta(days=15):
        raise OpenDataUnavailable(
            "Open-Meteo forecasts cover at most ~16 days ahead; choose an earlier analysis date.")
    return OPEN_METEO_ARCHIVE if analysis_date < today - timedelta(days=85) else OPEN_METEO_FORECAST


def fetch_weather(latitude: float, longitude: float, analysis_date: date_type) -> dict[str, Any]:
    """Hourly weather series for one site and day (cached; stale cache as fallback)."""
    key = f"{latitude:.3f},{longitude:.3f},{analysis_date.isoformat()}"
    fresh = cache.get("weather", key, max_age_s=WEATHER_CACHE_MAX_AGE_S)
    if fresh is not None:
        return {**fresh, "from_cache": True, "cache_note": "fresh"}
    try:
        body = _http_get_json(_weather_endpoint(analysis_date), {
            "latitude": round(latitude, 4), "longitude": round(longitude, 4),
            "hourly": HOURLY_VARS, "timezone": "auto",
            "start_date": analysis_date.isoformat(), "end_date": analysis_date.isoformat(),
        })
        hourly = body.get("hourly") or {}
        if not hourly.get("time") or not hourly.get("temperature_2m"):
            raise OpenDataUnavailable("Open-Meteo returned no hourly temperature data.")
        data = {"elevation_m": body.get("elevation"), "timezone": body.get("timezone"), "hourly": hourly}
        cache.put("weather", key, data)
        return {**data, "from_cache": False, "cache_note": "live"}
    except (OpenDataUnavailable, requests.RequestException, ValueError) as exc:
        stale = cache.get("weather", key, max_age_s=None)
        if stale is not None:
            logger.warning("Open-Meteo failed (%s); using cached copy.", exc)
            return {**stale, "from_cache": True, "cache_note": "stale (network unavailable)"}
        raise OpenDataUnavailable(f"Open-Meteo unavailable: {exc}") from exc


def _hour_index(times: list[str], hour_hhmm: str) -> int:
    try:
        target_h = int(hour_hhmm.split(":")[0])
    except (ValueError, IndexError):
        target_h = 14
    for i, t in enumerate(times):           # ISO "YYYY-MM-DDTHH:MM"
        if int(t[11:13]) == target_h:
            return i
    return min(target_h, len(times) - 1)


def _num(series: list, i: int) -> Optional[float]:
    try:
        v = series[i]
    except (IndexError, TypeError):
        return None
    return float(v) if isinstance(v, (int, float)) else None


# ----------------------------------------------------------- land cover ----

def _overpass_query(lat: float, lon: float, r: float) -> str:
    a = f"(around:{int(r)},{lat},{lon})"
    return (
        "[out:json][timeout:60];("
        f'way["building"]{a};way["highway"]{a};way["amenity"="parking"]{a};'
        f'way["landuse"]{a};way["natural"]{a};way["leisure"]{a};way["waterway"="riverbank"]{a};'
        f'relation["natural"="water"]{a};relation["landuse"]{a};relation["leisure"="park"]{a};'
        f'node["natural"="tree"]{a};'
        ");out geom;"
    )


def _project(lat0: float, lon0: float):
    m_lat = 111_320.0
    m_lon = 111_320.0 * math.cos(math.radians(lat0))
    return lambda lon, lat: ((lon - lon0) * m_lon, (lat - lat0) * m_lat)


def classify_landcover(elements: list[dict], lat: float, lon: float,
                       radius_m: float = LANDCOVER_RADIUS_M) -> dict[str, Any]:
    """Turn raw Overpass elements into impervious / vegetation / water percentages."""
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import polygonize, unary_union

    proj = _project(lat, lon)
    circle = Point(0, 0).buffer(radius_m, 32)
    circle_area = circle.area

    def pts(geom):
        return [proj(p["lon"], p["lat"]) for p in geom or [] if "lat" in p]

    def poly_from_way(el):
        c = pts(el.get("geometry"))
        if len(c) >= 4 and c[0] == c[-1]:
            try:
                g = Polygon(c)
                return g if g.is_valid else g.buffer(0)
            except Exception:  # noqa: BLE001
                return None
        return None

    def polys_from_relation(el):
        lines = []
        for m in el.get("members", []):
            if m.get("role") in ("outer", "") and m.get("geometry"):
                c = pts(m["geometry"])
                if len(c) >= 2:
                    lines.append(LineString(c))
        try:
            return list(polygonize(unary_union(lines))) if lines else []
        except Exception:  # noqa: BLE001
            return []

    buildings, hard_areas, roads, veg, water, semi = [], [], [], [], [], []   # semi: (geom, weight)
    trees = 0
    feature_count = 0

    for el in elements:
        tags = el.get("tags") or {}
        et = el.get("type")
        if et == "node":
            if tags.get("natural") == "tree" and "lat" in el:
                x, y = proj(el["lon"], el["lat"])
                veg.append(Point(x, y).buffer(3.0))
                trees += 1
            continue

        geoms = [poly_from_way(el)] if et == "way" else polys_from_relation(el)
        geoms = [g for g in geoms if g is not None and not g.is_empty]
        feature_count += 1

        if "building" in tags:
            buildings += geoms
        elif tags.get("highway") and et == "way":
            c = pts(el.get("geometry"))
            if len(c) >= 2 and not (len(c) >= 4 and c[0] == c[-1] and tags.get("area") == "yes"):
                width = ROAD_WIDTH_M.get(tags["highway"], 4)
                roads.append(LineString(c).buffer(width / 2.0, cap_style=2))
        elif tags.get("amenity") == "parking":
            hard_areas += geoms
        elif tags.get("natural") == "water" or tags.get("waterway") == "riverbank" or tags.get("landuse") in ("reservoir", "basin"):
            water += geoms
        elif tags.get("natural") in VEG_NATURAL or tags.get("landuse") in VEG_LANDUSE or tags.get("leisure") in VEG_LEISURE:
            veg += geoms
        elif tags.get("landuse") in HARD_LANDUSE:
            semi += [(g, HARD_LANDUSE[tags["landuse"]]) for g in geoms]

    def union_clip(gs):
        gs = [g for g in gs if g is not None and not g.is_empty]
        return unary_union(gs).intersection(circle) if gs else Polygon()

    water_u = union_clip(water)
    hard_u = union_clip(buildings + hard_areas + roads).difference(water_u)
    veg_u = union_clip(veg).difference(hard_u).difference(water_u)
    taken = unary_union([water_u, hard_u, veg_u])

    semi_impervious = 0.0
    for g, w in semi:
        part = g.intersection(circle).difference(taken)
        semi_impervious += part.area * w
        taken = unary_union([taken, part])

    seen_area = max(0.0, min(circle_area, taken.area))
    unmapped = max(0.0, circle_area - seen_area)

    impervious = hard_u.area + semi_impervious + unmapped * UNMAPPED_IMPERVIOUS_SHARE
    vegetation = veg_u.area + unmapped * UNMAPPED_VEGETATION_SHARE
    water_area = water_u.area

    coverage = seen_area / circle_area
    if feature_count >= 25 and coverage >= 0.35:
        confidence = "high"
    elif feature_count >= 8 and coverage >= 0.15:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "impervious_pct": round(100 * impervious / circle_area, 1),
        "tree_canopy_pct": round(100 * vegetation / circle_area, 1),   # vegetation cover (trees, parks, grass)
        "water_pct": round(100 * water_area / circle_area, 1),
        "osm_feature_count": feature_count,
        "osm_tree_nodes": trees,
        "mapped_coverage_pct": round(100 * coverage, 1),
        "confidence": confidence,
        "radius_m": radius_m,
    }


def fetch_landcover(latitude: float, longitude: float) -> dict[str, Any]:
    """Land cover around a site from OpenStreetMap (cached indefinitely - it barely changes)."""
    key = f"{latitude:.4f},{longitude:.4f},{int(LANDCOVER_RADIUS_M)}"
    cached = cache.get("landcover", key, max_age_s=None)
    if cached is not None:
        return {**cached, "from_cache": True}
    try:
        body = _http_post_overpass(_overpass_query(latitude, longitude, LANDCOVER_RADIUS_M))
        result = classify_landcover(body.get("elements", []), latitude, longitude)
    except (OpenDataUnavailable, requests.RequestException, ValueError) as exc:
        raise OpenDataUnavailable(f"OpenStreetMap land cover unavailable: {exc}") from exc
    cache.put("landcover", key, result)
    return {**result, "from_cache": False}


# ------------------------------------------------- microclimate + snapshot --

def microclimate_adjustment_c(impervious_pct: float, vegetation_pct: float, water_pct: float) -> float:
    """Bounded deg-C offset vs. a neutral reference site (transparent, documented)."""
    delta = (K_IMPERVIOUS * (impervious_pct / 100.0 - REF_IMPERVIOUS)
             - K_VEGETATION * (vegetation_pct / 100.0 - REF_VEGETATION)
             - K_WATER * (water_pct / 100.0))
    return round(max(-MAX_ADJUSTMENT_C, min(MAX_ADJUSTMENT_C, delta)), 2)


def get_site_snapshot(latitude: float, longitude: float, analysis_date: date_type,
                      analysis_hour: str) -> dict[str, Any]:
    """Everything HeatWise needs for one site, from free sources only.

    Raises OpenDataUnavailable only if weather itself is unobtainable. If just
    land cover fails we still return weather with a neutral land-cover prior and
    say so, rather than discarding good live data.
    """
    weather = fetch_weather(latitude, longitude, analysis_date)
    hourly = weather["hourly"]
    times = hourly["time"]
    i = _hour_index(times, analysis_hour)

    raw_temp = _num(hourly["temperature_2m"], i)
    if raw_temp is None:
        raise OpenDataUnavailable("Open-Meteo had no temperature for the requested hour.")
    rh = _num(hourly.get("relative_humidity_2m", []), i)
    ghi = _num(hourly.get("shortwave_radiation", []), i)
    dni = _num(hourly.get("direct_normal_irradiance", []), i)
    dhi = _num(hourly.get("diffuse_radiation", []), i)
    cloud = _num(hourly.get("cloud_cover", []), i)
    apparent = _num(hourly.get("apparent_temperature", []), i)

    land_note = None
    try:
        land = fetch_landcover(latitude, longitude)
    except OpenDataUnavailable as exc:
        land_note = str(exc)
        land = {"impervious_pct": 50.0, "tree_canopy_pct": 12.0, "water_pct": 0.0,
                "osm_feature_count": 0, "osm_tree_nodes": 0, "mapped_coverage_pct": 0.0,
                "confidence": "none", "radius_m": LANDCOVER_RADIUS_M, "from_cache": False}

    adj = microclimate_adjustment_c(land["impervious_pct"], land["tree_canopy_pct"], land["water_pct"])
    if land["confidence"] in ("low", "none"):
        adj = round(adj * 0.5, 2)         # don't over-trust sparse map data

    temperature_c = round(raw_temp + adj, 2)
    rh_eff = rh if rh is not None else 40.0

    series = []
    for h in range(5, 21):
        idx = next((k for k, t in enumerate(times) if int(t[11:13]) == h), None)
        if idx is None:
            continue
        t_raw = _num(hourly["temperature_2m"], idx)
        if t_raw is None:
            continue
        t_adj = t_raw + adj
        rh_h = _num(hourly.get("relative_humidity_2m", []), idx) or rh_eff
        series.append({"hour": h, "temperature_c": round(t_adj, 2),
                       "heat_index_c": heat_index_c(t_adj, rh_h),
                       "solar_ghi": _num(hourly.get("shortwave_radiation", []), idx)})

    return {
        "raw_air_temperature_c": round(raw_temp, 2),
        "adjustment_c": adj,
        "temperature_c": temperature_c,
        "relative_humidity_pct": rh,
        "heat_index_c": heat_index_c(temperature_c, rh_eff),
        "apparent_temp_c": apparent,
        "wet_bulb_c": wet_bulb_c(temperature_c, rh_eff),
        "cloud_cover_pct": cloud,
        "solar_ghi": ghi, "solar_dni": dni, "solar_dhi": dhi,
        "elevation_m": weather.get("elevation_m"),
        "land": land, "land_note": land_note,
        "hourly": series,
        "weather_from_cache": weather["from_cache"], "weather_cache_note": weather["cache_note"],
    }
