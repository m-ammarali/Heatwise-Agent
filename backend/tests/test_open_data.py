"""Tests for the free open-data provider. All HTTP is mocked (response shapes
mirror Open-Meteo's documented JSON and Overpass `out geom` output)."""
import datetime

import pytest

from services import cache, open_data_service as od, providers


def _om_body(base=38.0):
    times = [f"2026-07-15T{h:02d}:00" for h in range(24)]
    temp = [base - 8 + 8 * max(0.0, 1 - abs(h - 15) / 9) for h in range(24)]
    ghi = [max(0.0, 900 * max(0.0, 1 - abs(h - 13) / 7)) for h in range(24)]
    return {"elevation": 215.0, "timezone": "Asia/Karachi", "hourly": {
        "time": times, "temperature_2m": temp, "relative_humidity_2m": [30.0] * 24,
        "apparent_temperature": [t + 2 for t in temp], "shortwave_radiation": ghi,
        "direct_normal_irradiance": [g * 0.8 for g in ghi], "diffuse_radiation": [g * 0.15 for g in ghi],
        "cloud_cover": [10.0] * 24}}


def _sq(lat, lon, half_m):
    d_lat = half_m / 111320.0
    d_lon = half_m / (111320.0 * 0.85)
    pts = [(lon - d_lon, lat - d_lat), (lon + d_lon, lat - d_lat), (lon + d_lon, lat + d_lat),
           (lon - d_lon, lat + d_lat), (lon - d_lon, lat - d_lat)]
    return [{"lat": y, "lon": x} for x, y in pts]


LAT, LON = 31.5889, 74.3147


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)


def test_heat_index_and_wet_bulb_sane():
    assert od.heat_index_c(20.0, 50.0) == 20.0               # below regression range
    assert 42 < od.heat_index_c(38.0, 40.0) < 45              # NWS chart: ~100F @ 40% RH ~= 109-110F ~= 43C
    assert od.heat_index_c(38.0, 60.0) > od.heat_index_c(38.0, 20.0)
    assert 20 < od.wet_bulb_c(35.0, 50.0) < 30                # Stull sanity range


def test_landcover_paved_vs_green():
    paved = [{"type": "way", "tags": {"building": "yes"}, "geometry": _sq(LAT, LON, 120)},
             {"type": "way", "tags": {"highway": "primary"}, "geometry": [
                 {"lat": LAT - 0.002, "lon": LON}, {"lat": LAT + 0.002, "lon": LON}]}]
    green = [{"type": "way", "tags": {"leisure": "park"}, "geometry": _sq(LAT, LON, 200)}]
    p = od.classify_landcover(paved, LAT, LON)
    g = od.classify_landcover(green, LAT, LON)
    assert p["impervious_pct"] > g["impervious_pct"]
    assert g["tree_canopy_pct"] > p["tree_canopy_pct"]
    assert g["tree_canopy_pct"] > 60
    assert p["confidence"] == "low"                           # only 2 features -> honest low confidence


def test_microclimate_adjustment_is_bounded_and_directional():
    hot = od.microclimate_adjustment_c(95, 0, 0)
    cool = od.microclimate_adjustment_c(10, 70, 10)
    assert 0 < hot <= od.MAX_ADJUSTMENT_C
    assert -od.MAX_ADJUSTMENT_C <= cool < 0


def test_snapshot_combines_weather_and_landcover(monkeypatch):
    monkeypatch.setattr(od, "_http_get_json", lambda url, params: _om_body())
    monkeypatch.setattr(od, "_http_post_overpass", lambda q: {"elements": [
        {"type": "way", "tags": {"building": "yes"}, "geometry": _sq(LAT, LON, 200)}]})
    s = od.get_site_snapshot(LAT, LON, datetime.date(2026, 7, 15), "14:00")
    assert s["temperature_c"] != s["raw_air_temperature_c"] or s["adjustment_c"] == 0
    assert s["solar_ghi"] > 500 and s["hourly"] and s["hourly"][0]["hour"] == 5
    assert s["land"]["impervious_pct"] > 50


def test_weather_falls_back_to_stale_cache_when_network_dies(monkeypatch):
    d = datetime.date(2026, 7, 15)
    monkeypatch.setattr(od, "_http_get_json", lambda url, params: _om_body())
    od.fetch_weather(LAT, LON, d)                              # warms cache

    def boom(url, params):
        raise od.OpenDataUnavailable("offline")
    monkeypatch.setattr(od, "_http_get_json", boom)
    monkeypatch.setattr(od, "WEATHER_CACHE_MAX_AGE_S", -1)     # treat cache as stale
    w = od.fetch_weather(LAT, LON, d)
    assert w["from_cache"] and "stale" in w["cache_note"]


def test_no_cache_and_no_network_raises(monkeypatch):
    def boom(url, params):
        raise od.OpenDataUnavailable("offline")
    monkeypatch.setattr(od, "_http_get_json", boom)
    with pytest.raises(od.OpenDataUnavailable):
        od.fetch_weather(LAT, LON, datetime.date(2026, 7, 15))


def test_forecast_horizon_enforced():
    far = datetime.date.today() + datetime.timedelta(days=40)
    with pytest.raises(od.OpenDataUnavailable):
        od._weather_endpoint(far)


def test_full_analysis_with_open_data_and_pdf(monkeypatch, tmp_path):
    from agent import orchestrator
    from models.schemas import AnalyzeRequest, LocationIn

    monkeypatch.setenv("DATA_PROVIDER", "open_data")
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setattr(orchestrator, "OUTPUTS_DIR", tmp_path)
    monkeypatch.setattr(od, "_http_get_json", lambda url, params: _om_body(40.0))

    def overpass(q):
        # Same mocked area for both sites except one is a park
        return {"elements": [{"type": "way", "tags": {"building": "yes"}, "geometry": _sq(LAT, LON, 200)}]}
    monkeypatch.setattr(od, "_http_post_overpass", overpass)

    req = AnalyzeRequest(
        locations=[LocationIn(name="Walled City", latitude=LAT, longitude=LON),
                   LocationIn(name="Other", latitude=31.5134, longitude=74.3335)],
        analysis_date=datetime.date(2026, 7, 15))
    resp = orchestrator.run_analysis(req)

    assert resp.demo_mode is False
    assert all(r.data_source == "open_data" for r in resp.results)
    assert "Open-Meteo" in resp.data_provider
    r0 = resp.results[0]
    assert any("microclimate" in e.label.lower() for e in r0.evidence)
    assert len(r0.work_windows) >= 2                           # derived from hourly series
    hot = [r for r in resp.results if r.risk_level in ("HIGH", "CRITICAL")]
    assert hot, "a 40C site should trigger the conditional deep investigation"
    assert all(r.heat_intelligence.pdf_available for r in hot)
    assert list(tmp_path.glob("heat_intelligence_*.pdf"))


def test_low_risk_site_skips_deep_investigation(monkeypatch, tmp_path):
    from agent import orchestrator
    from models.schemas import AnalyzeRequest, LocationIn

    monkeypatch.setenv("DATA_PROVIDER", "open_data")
    monkeypatch.setattr(orchestrator, "OUTPUTS_DIR", tmp_path)
    monkeypatch.setattr(od, "_http_get_json", lambda url, params: _om_body(24.0))
    monkeypatch.setattr(od, "_http_post_overpass", lambda q: {"elements": [
        {"type": "way", "tags": {"leisure": "park"}, "geometry": _sq(LAT, LON, 200)}]})
    resp = orchestrator.run_analysis(AnalyzeRequest(
        locations=[LocationIn(name="Cool Park", latitude=LAT, longitude=LON)],
        analysis_date=datetime.date(2026, 7, 15)))
    r = resp.results[0]
    assert r.risk_level in ("LOW", "MODERATE")
    assert r.heat_intelligence.requested is False and not list(tmp_path.glob("*.pdf"))


def test_network_failure_falls_back_to_demo_per_site(monkeypatch):
    from agent import orchestrator
    from models.schemas import AnalyzeRequest, LocationIn

    def boom(url, params):
        raise od.OpenDataUnavailable("offline")
    monkeypatch.setenv("DATA_PROVIDER", "open_data")
    monkeypatch.setattr(od, "_http_get_json", boom)
    resp = orchestrator.run_analysis(AnalyzeRequest(
        locations=[LocationIn(name="Greater Iqbal Park", latitude=31.592, longitude=74.3088)],
        analysis_date=datetime.date(2026, 7, 15)))
    assert resp.demo_mode is True and resp.results[0].data_source == "demo"


def test_demo_provider_setting_never_touches_network(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "demo")
    with pytest.raises(providers.ProviderUnavailable):
        providers.get_provider()
