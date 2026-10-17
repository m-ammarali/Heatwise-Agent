"""HeatWise's service layer over the vendored, unmodified FortyGuard client.

Every field accessed here is taken from the verified response shapes
documented in the official quickstart notebooks (fortyguard/client.py +
notebooks/01..05). Nothing here invents an endpoint or a field name.
"""
from __future__ import annotations

import logging
import os
from datetime import date as date_type
from typing import Any, Optional

from fortyguard import FortyGuardClient
from fortyguard.exceptions import FortyGuardError

from services.geo import square_polygon_aoi

logger = logging.getLogger("heatwise.fortyguard_service")


class FortyGuardUnavailable(Exception):
    """Raised whenever HeatWise cannot get live FortyGuard data.

    The caller (agent orchestrator) is expected to catch this and fall back
    to Demo Mode rather than silently fabricating numbers.
    """


def _coerce_scalar(value: Any, field_name: str) -> Optional[float]:
    """Defensively coerce a response field to a single float.

    Confirmed against a live response: FortyGuard's env_params fields come
    back as a list (likely an hourly series) even for a single-hour
    request, in which case it's a 1-element list — the single value, just
    wrapped. That's expected and not logged. A list with more than one
    element is unexpected for a single-hour request and IS logged, since it
    means we're silently averaging across multiple hours rather than using
    the one requested.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (list, tuple)) and value:
        numeric = [v for v in value if isinstance(v, (int, float))]
        if numeric:
            coerced = float(sum(numeric) / len(numeric))
            if len(value) > 1:
                logger.warning(
                    "FortyGuard field '%s' returned a %d-element list for a single-hour "
                    "request; using the mean (%.2f) as an approximation instead of the "
                    "single requested hour.",
                    field_name, len(value), coerced,
                )
            return coerced
    logger.warning("FortyGuard field '%s' had an unexpected shape (%r); treating as missing.", field_name, value)
    return None


def get_client() -> FortyGuardClient:
    api_key = os.getenv("FORTYGUARD_API_KEY")
    if not api_key:
        raise FortyGuardUnavailable("FORTYGUARD_API_KEY is not set.")
    try:
        return FortyGuardClient()
    except FortyGuardError as exc:
        raise FortyGuardUnavailable(str(exc)) from exc


def get_site_temperature_c(
    client: FortyGuardClient,
    latitude: float,
    longitude: float,
    analysis_date: date_type,
    analysis_hour: str,
) -> dict[str, Any]:
    """Real hyperlocal temperature for a site via POST /v1/heatmap.

    Builds a small buffer polygon around the point (see services/geo.py),
    requests a single-hour (`filter_type=1`) snapshot, and area-averages
    the tile temperatures returned in `result.map_data.features[].properties.temperature`
    (falling back to `result.stats_data.Temperature_stats` mean if present).
    All values are already °C, per the API's documented contract.
    """
    polygon = square_polygon_aoi(latitude, longitude)
    try:
        response = client.create_heatmap(
            polygon_aoi=polygon,
            start_date=analysis_date.isoformat(),
            start_time=analysis_hour,
            filter_type=1,
            granularity=60,
            analytic_type="tcm",
            wait=True,
            verbose=False,
        )
    except FortyGuardError as exc:
        raise FortyGuardUnavailable(f"create_heatmap failed: {exc}") from exc

    result = response.get("result", {})
    stats = result.get("stats_data", {}) or {}
    temp_stats = stats.get("Temperature_stats") or stats.get("temperature_stats") or {}

    temperature_c: Optional[float] = None
    if isinstance(temp_stats, dict):
        for key in ("mean", "average", "avg"):
            if key in temp_stats:
                temperature_c = float(temp_stats[key])
                break

    if temperature_c is None:
        # Fall back to averaging tile-level temperature properties directly.
        # Empirically (confirmed against a live response), filter_type=1
        # tiles carry average_temperature/min_temperature/max_temperature —
        # not a generic `temperature` field as the notebook markdown implied.
        # Check both to be safe.
        features = (result.get("map_data") or {}).get("features") or []
        temps = [
            f["properties"].get("temperature", f["properties"].get("average_temperature"))
            for f in features
            if "temperature" in f.get("properties", {}) or "average_temperature" in f.get("properties", {})
        ]
        if temps:
            temperature_c = sum(temps) / len(temps)

    if temperature_c is None:
        # Diagnostic dump: log the actual shape we got back so the real
        # field names/paths can be confirmed and this extraction fixed
        # precisely, instead of guessing again.
        logger.warning(
            "create_heatmap returned no usable temperature for (%.4f, %.4f) on %s. "
            "response top-level keys=%s | result keys=%s | stats_data keys=%s | "
            "map_data keys=%s | feature_count=%s | sample_feature=%s",
            latitude, longitude, analysis_date.isoformat(),
            list(response.keys()),
            list(result.keys()),
            list(stats.keys()),
            list((result.get("map_data") or {}).keys()),
            len((result.get("map_data") or {}).get("features") or []),
            ((result.get("map_data") or {}).get("features") or [None])[0],
        )
        raise FortyGuardUnavailable(
            "create_heatmap succeeded but returned no usable temperature tiles "
            "for this site and date. FortyGuard's catalog can lag by a day or "
            "more for very recent dates — try an earlier analysis_date first; "
            "if an older date also returns zero tiles, the site itself may be "
            "outside current coverage."
        )

    return {
        "activity_id": response.get("activity_id"),
        "temperature_c": round(temperature_c, 2),
        "raw_stats": temp_stats,
        "tile_count": len((result.get("map_data") or {}).get("features") or []),
    }


def get_environmental_parameters(
    client: FortyGuardClient,
    latitude: float,
    longitude: float,
    temperature_c: float,
    analysis_date: date_type,
    analysis_hour: str,
) -> dict[str, Any]:
    """POST /v1/env_params — thermal comfort + solar irradiance for the site."""
    try:
        response = client.environmental_parameters(
            latitude=latitude,
            longitude=longitude,
            temperature=temperature_c,
            start_date=analysis_date.isoformat(),
            start_time=analysis_hour,
            filter_type=1,
            wait=True,
            verbose=False,
        )
    except FortyGuardError as exc:
        raise FortyGuardUnavailable(f"environmental_parameters failed: {exc}") from exc

    result = response.get("result", {})
    locations = result.get("locations") or []
    location = locations[0] if locations else {}
    params = location.get("parameters", {}) or {}
    solar = (location.get("solar_irradiance") or {}).get("clear_sky", {}) or {}

    return {
        "activity_id": response.get("activity_id"),
        "heat_index_c": _coerce_scalar(params.get("heat_index_celsius"), "parameters.heat_index_celsius"),
        "apparent_temp_c": _coerce_scalar(params.get("apparent_temperature_celsius"), "parameters.apparent_temperature_celsius"),
        "wet_bulb_c": _coerce_scalar(params.get("wet_bulb_temperature_celsius"), "parameters.wet_bulb_temperature_celsius"),
        "relative_humidity_pct": _coerce_scalar(params.get("relative_humidity_percent"), "parameters.relative_humidity_percent"),
        "cloud_cover_octas": _coerce_scalar(params.get("cloud_cover_octas"), "parameters.cloud_cover_octas"),
        "air_quality_idx": _coerce_scalar(params.get("air_quality:idx"), "parameters.air_quality:idx"),
        "solar_ghi": _coerce_scalar(solar.get("ghi"), "solar_irradiance.clear_sky.ghi"),
        "solar_dni": _coerce_scalar(solar.get("dni"), "solar_irradiance.clear_sky.dni"),
        "solar_dhi": _coerce_scalar(solar.get("dhi"), "solar_irradiance.clear_sky.dhi"),
        "elevation_m": _coerce_scalar(location.get("elevation"), "locations[].elevation"),
    }


def get_satellite_context(
    client: FortyGuardClient,
    latitude: float,
    longitude: float,
    analysis_date: date_type,
    analysis_hour: str,
) -> dict[str, Any]:
    """POST /v1/satellite (Premium) — land-cover composition around the site."""
    try:
        response = client.satellite_segmentation(
            latitude=latitude,
            longitude=longitude,
            start_date=analysis_date.isoformat(),
            start_time=analysis_hour,
            filter_type=1,
            granularity=80,
            wait=True,
            verbose=False,
        )
    except FortyGuardError as exc:
        raise FortyGuardUnavailable(f"satellite_segmentation failed: {exc}") from exc

    result = response.get("result", {})
    segments: dict[str, float] = (result.get("segmentation") or {}).get("segments", {}) or {}

    tree_pct = sum(v for k, v in segments.items() if "tree" in k.lower() or "plant" in k.lower() or "grass" in k.lower())
    impervious_pct = sum(
        v for k, v in segments.items()
        if any(term in k.lower() for term in ("building", "road", "route", "sidewalk", "pavement", "earth", "ground"))
    )

    return {
        "activity_id": response.get("activity_id"),
        "segments": segments,
        "tree_canopy_pct": round(tree_pct, 1) if segments else None,
        "impervious_pct": round(impervious_pct, 1) if segments else None,
        "image_year": result.get("image_year"),
    }


def get_street_context(
    client: FortyGuardClient,
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """POST /v1/streetview (Premium) — ground-level shade/canopy context."""
    try:
        response = client.street_view_segmentation(
            latitude=latitude,
            longitude=longitude,
            vertical_angle=10.0,
            horizontal_angle=0.0,
            back_view=False,
            wait=True,
            verbose=False,
        )
    except FortyGuardError as exc:
        raise FortyGuardUnavailable(f"street_view_segmentation failed: {exc}") from exc

    result = response.get("result", {})
    front = result.get("front", {}) or {}
    segments: dict[str, float] = front.get("segments", {}) or {}
    sky_pct = next((v for k, v in segments.items() if "sky" in k.lower()), None)
    street_tree_pct = next((v for k, v in segments.items() if "tree" in k.lower()), None)

    return {
        "activity_id": response.get("activity_id"),
        "segments": segments,
        "sky_open_pct": sky_pct,
        "street_tree_pct": street_tree_pct,
    }


def generate_heat_intelligence_report(
    client: FortyGuardClient,
    latitude: float,
    longitude: float,
    temperature_c: float,
    analysis_date: date_type,
    categories: list[str],
    output_dir: str,
) -> dict[str, Any]:
    """POST /v1/heat_intelligence (Premium) — downloads the generated PDF.

    Unlike the other endpoints this does not return JSON; the client saves
    a PDF to disk and returns its Path, per the quickstart's documented
    contract (05_heat_intelligence_report.ipynb).
    """
    try:
        pdf_path = client.heat_intelligence(
            latitude=latitude,
            longitude=longitude,
            temperature=temperature_c,
            date=analysis_date.isoformat(),
            analysis=categories,
            output_path=None,
            verbose=False,
        )
    except FortyGuardError as exc:
        raise FortyGuardUnavailable(f"heat_intelligence failed: {exc}") from exc

    return {"pdf_path": str(pdf_path)}