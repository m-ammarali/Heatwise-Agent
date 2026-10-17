import datetime

from agent.orchestrator import run_analysis
from models.schemas import AnalyzeRequest, LocationIn


def test_multi_location_ranks_by_risk_score():
    req = AnalyzeRequest(
        locations=[
            LocationIn(name="Phoenix Construction Zone", latitude=33.4484, longitude=-112.0740),
            LocationIn(name="Papago Park Delivery Hub", latitude=33.4600, longitude=-111.9470),
        ],
        analysis_date=datetime.date(2026, 7, 15),
        demo_mode=True,
    )
    resp = run_analysis(req)
    scores = [r.risk_score for r in resp.results]
    assert scores == sorted(scores)
    assert resp.preferred_site == resp.results[0].name


def test_single_location_still_produces_decision_summary():
    req = AnalyzeRequest(
        locations=[LocationIn(name="Scottsdale Work Area", latitude=33.4942, longitude=-111.9261)],
        analysis_date=datetime.date(2026, 7, 15),
        demo_mode=True,
    )
    resp = run_analysis(req)
    assert resp.preferred_site == "Scottsdale Work Area"
    assert len(resp.decision_summary) > 0


def test_decision_trace_is_nonempty_and_ordered():
    req = AnalyzeRequest(
        locations=[LocationIn(name="Phoenix Construction Zone", latitude=33.4484, longitude=-112.0740)],
        analysis_date=datetime.date(2026, 7, 15),
        demo_mode=True,
    )
    resp = run_analysis(req)
    steps = [s.step for s in resp.decision_trace]
    assert steps == list(range(1, len(steps) + 1))
