import os
import datetime

from fastapi.testclient import TestClient


def test_no_live_provider_falls_back_gracefully(monkeypatch):
    # Simulate "no live data source" deterministically, with no real network call.
    from services import providers

    def _raise():
        raise providers.ProviderUnavailable("no provider (test)")

    monkeypatch.setattr(providers, "get_provider", _raise)

    from main import app
    client = TestClient(app)

    r = client.post("/api/analyze", json={
        "locations": [{"name": "Phoenix Construction Zone", "latitude": 33.4484, "longitude": -112.0740}],
        "analysis_date": "2026-07-15",
        "analysis_hour": "14:00",
        "demo_mode": False,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["demo_mode"] is True  # no provider -> falls back, doesn't error


def test_invalid_location_returns_422():
    from main import app
    client = TestClient(app)
    r = client.post("/api/analyze", json={
        "locations": [{"name": "Bad", "latitude": 999.0, "longitude": -112.0}],
        "analysis_date": "2026-07-15",
    })
    assert r.status_code == 422


def test_history_detail_404_for_unknown_id():
    from main import app
    client = TestClient(app)
    r = client.get("/api/history/does-not-exist")
    assert r.status_code == 404


def test_status_endpoint_never_leaks_api_keys(monkeypatch):
    monkeypatch.setenv("FORTYGUARD_API_KEY", "secret-key-value")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "secret-qwen-value")
    from main import app
    client = TestClient(app)
    r = client.get("/api/status")
    assert "secret-key-value" not in r.text
    assert "secret-qwen-value" not in r.text