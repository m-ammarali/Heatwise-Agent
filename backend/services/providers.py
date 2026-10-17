"""Pluggable data providers for the HeatWise agent.

DATA_PROVIDER (env) selects the source:
  open_data  (default)  free: Open-Meteo + OpenStreetMap, no API key
  fortyguard            original FortyGuard API (needs FORTYGUARD_API_KEY)
  demo                  never call the network; bundled demo data only

Every provider exposes the same five steps the agent uses
(observe / analyze / landcover / hourly / report), so the orchestrator,
risk model, decision engine and UI do not care where the data came from.
"""
from __future__ import annotations

import os
import threading
from datetime import date as date_type
from typing import Any, Optional

from services import fortyguard_service as fg
from services import open_data_service as od
from services import report_service


class ProviderUnavailable(Exception):
    """Provider cannot supply data for this request (caller falls back to demo)."""


def configured_provider_name() -> str:
    return (os.getenv("DATA_PROVIDER") or "open_data").strip().lower()


# --------------------------------------------------------------- open data --

class OpenDataProvider:
    name = "open_data"
    label = "Open-Meteo + OpenStreetMap (free, no key)"
    data_source = "open_data"          # value reported on each LocationResult

    desc_observe = "retrieving hourly site weather (Open-Meteo)"
    desc_analyze = "computing heat index, wet-bulb and solar irradiance from the weather series"
    desc_landcover = "mapping land cover within 250 m (OpenStreetMap / Overpass)"
    desc_report = "generating Heat Intelligence Brief (local PDF)"

    def __init__(self) -> None:
        self._snaps: dict[tuple, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _snapshot(self, loc, d: date_type, hour: str) -> dict[str, Any]:
        k = (loc.name, round(loc.latitude, 5), round(loc.longitude, 5), d.isoformat(), hour)
        with self._lock:
            if k in self._snaps:
                return self._snaps[k]
        try:
            snap = od.get_site_snapshot(loc.latitude, loc.longitude, d, hour)
        except od.OpenDataUnavailable as exc:
            raise ProviderUnavailable(str(exc)) from exc
        with self._lock:
            self._snaps[k] = snap
        return snap

    def observe(self, loc, d, hour) -> dict[str, Any]:
        s = self._snapshot(loc, d, hour)
        return {"temperature_c": s["temperature_c"], "raw_air_temperature_c": s["raw_air_temperature_c"],
                "adjustment_c": s["adjustment_c"]}

    def analyze(self, loc, observed, d, hour) -> dict[str, Any]:
        s = self._snapshot(loc, d, hour)
        return {k: s[k] for k in ("heat_index_c", "relative_humidity_pct", "solar_ghi", "solar_dni", "solar_dhi")}

    def landcover(self, loc, observed, d, hour) -> dict[str, Any]:
        land = self._snapshot(loc, d, hour)["land"]
        return {"tree_canopy_pct": land["tree_canopy_pct"], "impervious_pct": land["impervious_pct"]}

    def hourly(self, loc, d, hour) -> Optional[list[dict[str, Any]]]:
        return self._snapshot(loc, d, hour)["hourly"] or None

    def extra_evidence(self, loc, d, hour) -> list[tuple[str, str, str]]:
        s = self._snapshot(loc, d, hour)
        land = s["land"]
        adj = s["adjustment_c"]
        out: list[tuple[str, str, str]] = [(
            "Modelled microclimate adjustment",
            "up" if adj > 0.2 else "down" if adj < -0.2 else "neutral",
            f"Regional air temperature {s['raw_air_temperature_c']:.1f}°C adjusted by {adj:+.1f}°C for this site's "
            f"land cover (impervious {land['impervious_pct']:.0f}%, vegetation {land['tree_canopy_pct']:.0f}%, "
            f"water {land['water_pct']:.0f}%). This is a modelled estimate, not a sensor measurement.",
        )]
        conf = land["confidence"]
        if conf in ("low", "none"):
            out.append(("Limited map data", "neutral",
                        "OpenStreetMap has few mapped features around this site, so land-cover values lean on "
                        "documented defaults and the adjustment was halved. Treat the ranking as indicative."
                        + (f" ({s['land_note']})" if s.get("land_note") else "")))
        else:
            out.append(("Land-cover data confidence", "neutral",
                        f"{conf.capitalize()} confidence: {land['osm_feature_count']} OpenStreetMap features "
                        f"mapped within {land['radius_m']:.0f} m."))
        if s.get("weather_from_cache") and "stale" in str(s.get("weather_cache_note")):
            out.append(("Cached weather data", "neutral",
                        "Live weather could not be reached; the last stored Open-Meteo response was used."))
        return out

    def report(self, ctx: dict[str, Any], output_dir: str) -> dict[str, Any]:
        try:
            return report_service.generate_heat_brief(ctx, output_dir)
        except Exception as exc:  # noqa: BLE001
            raise ProviderUnavailable(f"report generation failed: {exc}") from exc


# -------------------------------------------------------------- FortyGuard --

class FortyGuardProvider:
    name = "fortyguard"
    label = "FortyGuard Temperature API"
    data_source = "live"

    desc_observe = "retrieving hyperlocal temperature intelligence (POST /v1/heatmap)"
    desc_analyze = "retrieving environmental parameters (POST /v1/env_params)"
    desc_landcover = "retrieving satellite segmentation for land-cover context (POST /v1/satellite)"
    desc_report = "generating targeted Heat Intelligence report (POST /v1/heat_intelligence)"

    def __init__(self, client) -> None:
        self.client = client

    def _wrap(self, fn, *a, **kw):
        try:
            return fn(*a, **kw)
        except fg.FortyGuardUnavailable as exc:
            raise ProviderUnavailable(str(exc)) from exc

    def observe(self, loc, d, hour):
        return self._wrap(fg.get_site_temperature_c, self.client, loc.latitude, loc.longitude, d, hour)

    def analyze(self, loc, observed, d, hour):
        return self._wrap(fg.get_environmental_parameters, self.client, loc.latitude, loc.longitude,
                          observed["temperature_c"], d, hour)

    def landcover(self, loc, observed, d, hour):
        return self._wrap(fg.get_satellite_context, self.client, loc.latitude, loc.longitude, d, hour)

    def hourly(self, loc, d, hour):
        return None

    def extra_evidence(self, loc, d, hour):
        return []

    def report(self, ctx, output_dir):
        return self._wrap(fg.generate_heat_intelligence_report, self.client, ctx["latitude"], ctx["longitude"],
                          ctx["temperature_c"], date_type.fromisoformat(ctx["analysis_date"]),
                          ctx["categories"], output_dir)


# ----------------------------------------------------------------- factory --

def get_provider():
    """Return a provider instance, or raise ProviderUnavailable (-> Demo Mode)."""
    name = configured_provider_name()
    if name in ("demo", "none", "offline"):
        raise ProviderUnavailable("DATA_PROVIDER=demo: network data sources disabled.")
    if name == "fortyguard":
        try:
            return FortyGuardProvider(fg.get_client())
        except fg.FortyGuardUnavailable as exc:
            raise ProviderUnavailable(str(exc)) from exc
    return OpenDataProvider()
