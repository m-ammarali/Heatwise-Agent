"""HeatWise Agent orchestrator.

Implements the OBSERVE -> ANALYZE -> INVESTIGATE -> DECIDE -> ACT workflow
described in the product brief, with intelligent tool selection: cheap calls
always run, expensive ones (Heat Intelligence) only run when risk is
HIGH/CRITICAL or explicitly requested.

Data comes from a pluggable provider (services/providers.py): free
Open-Meteo + OpenStreetMap by default, FortyGuard optionally. Falls back to
Demo Mode per-location if a live call fails, and always labels which data
source was actually used — it never silently swaps live data for fake data.
"""
from __future__ import annotations

import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent import demo_data
from agent.decision_engine import (
    build_evidence,
    generate_action_plan,
    recommend_safe_work_window,
    should_run_heat_intelligence,
    windows_from_hourly,
)
from agent.risk_scoring import RiskComponents, calculate_heat_risk, primary_driver
from models.schemas import (
    EvidenceSignal,
    AnalyzeRequest,
    AnalyzeResponse,
    DecisionTraceStep,
    HeatIntelligenceInfo,
    LocationIn,
    LocationResult,
)
from services import providers, qwen_service
from services.geo import celsius_to_fahrenheit

logger = logging.getLogger("heatwise.orchestrator")

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"


class _Trace:
    def __init__(self) -> None:
        self._steps: list[str] = []

    def add(self, description: str) -> None:
        self._steps.append(description)

    def as_list(self) -> list[DecisionTraceStep]:
        return [DecisionTraceStep(step=i + 1, description=d) for i, d in enumerate(self._steps)]


def _analyze_one_location(
    loc: LocationIn,
    req: AnalyzeRequest,
    provider: Any,
    trace: _Trace,
) -> LocationResult:
    data_source = "demo"
    used_demo = req.demo_mode or provider is None

    observed: dict[str, Any] = {}
    env: dict[str, Any] = {}
    sat: dict[str, Any] = {}
    hourly = None
    extra_evidence: list[tuple[str, str, str]] = []

    if not used_demo:
        try:
            trace.add(f"[{loc.name}] OBSERVE — {provider.desc_observe}.")
            observed = provider.observe(loc, req.analysis_date, req.analysis_hour)
            data_source = provider.data_source

            trace.add(f"[{loc.name}] ANALYZE — {provider.desc_analyze}.")
            env = provider.analyze(loc, observed, req.analysis_date, req.analysis_hour)
        except providers.ProviderUnavailable as exc:
            logger.warning("Live data call failed for %s, falling back to demo: %s", loc.name, exc)
            trace.add(f"[{loc.name}] Live data call failed ({exc}); falling back to Demo Mode for this site.")
            used_demo = True
            data_source = "demo"

    if used_demo:
        demo = demo_data.demo_site_for(loc.name, loc.latitude, loc.longitude)
        observed = {"temperature_c": demo["temperature_c"]}
        env = {
            "heat_index_c": demo["heat_index_c"],
            "relative_humidity_pct": demo["relative_humidity_pct"],
            "solar_ghi": demo["solar_ghi"],
            "solar_dni": demo["solar_dni"],
            "solar_dhi": demo["solar_dhi"],
        }
        sat = {"tree_canopy_pct": demo["tree_canopy_pct"], "impervious_pct": demo["impervious_pct"]}
        trace.add(f"[{loc.name}] Using Demo Mode data (bundled illustrative scenario, not live data).")

    temperature_c = observed["temperature_c"]

    components = RiskComponents(
        temperature_c=temperature_c,
        heat_index_c=env.get("heat_index_c"),
        solar_ghi=env.get("solar_ghi"),
        tree_canopy_pct=sat.get("tree_canopy_pct"),
        impervious_pct=sat.get("impervious_pct"),
    )

    # ANALYZE: land-cover context — feeds the vegetation/impervious terms of the score.
    if not used_demo:
        try:
            trace.add(f"[{loc.name}] ANALYZE — {provider.desc_landcover}.")
            sat = provider.landcover(loc, observed, req.analysis_date, req.analysis_hour)
            components.tree_canopy_pct = sat.get("tree_canopy_pct")
            components.impervious_pct = sat.get("impervious_pct")
            hourly = provider.hourly(loc, req.analysis_date, req.analysis_hour)
            extra_evidence = provider.extra_evidence(loc, req.analysis_date, req.analysis_hour)
        except providers.ProviderUnavailable as exc:
            trace.add(f"[{loc.name}] Land-cover context unavailable ({exc}); continuing without it.")

    risk = calculate_heat_risk(components)
    trace.add(f"[{loc.name}] Calculated HeatWise Operational Risk Score: {risk.score} ({risk.level}).")

    evidence = build_evidence(components, risk)
    for label, direction, detail in extra_evidence:
        evidence.append(EvidenceSignal(label=label, direction=direction, detail=detail))
    driver = primary_driver(risk, components)

    # DECIDE / ACT (windows are built early so the report can include them)
    work_windows = []
    if hourly:
        work_windows = windows_from_hourly(hourly, components.tree_canopy_pct, components.impervious_pct)
        if work_windows:
            trace.add(f"[{loc.name}] Built work windows from the hourly forecast, scored with the same risk model.")
    if not work_windows:
        work_windows = recommend_safe_work_window(risk.level, req.analysis_hour)
    action_plan = generate_action_plan(risk.level, evidence)

    # INVESTIGATE: intelligent tool selection for the expensive deep-dive report.
    run_hi, categories, hi_reason = should_run_heat_intelligence(risk.level, req.deep_investigation)
    trace.add(f"[{loc.name}] Tool-selection decision: {hi_reason}")

    hi_info = HeatIntelligenceInfo(requested=run_hi, categories=categories, reason=hi_reason)
    if run_hi and not used_demo:
        try:
            trace.add(f"[{loc.name}] INVESTIGATE — {provider.desc_report} ({', '.join(categories)}).")
            OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
            ctx = {
                "name": loc.name, "latitude": loc.latitude, "longitude": loc.longitude,
                "analysis_date": req.analysis_date.isoformat(), "analysis_hour": req.analysis_hour,
                "temperature_c": temperature_c,
                "raw_air_temperature_c": observed.get("raw_air_temperature_c", temperature_c),
                "adjustment_c": observed.get("adjustment_c", 0.0),
                "risk_score": risk.score, "risk_level": risk.level, "primary_driver": driver,
                "breakdown": risk.breakdown, "weights": risk.weights,
                "evidence": [(e.label, e.direction, e.detail) for e in evidence],
                "work_windows": [(w.label, w.start, w.end, w.note) for w in work_windows],
                "action_plan": [(a.priority, a.action, a.reason) for a in action_plan],
                "land": {"impervious_pct": components.impervious_pct or 0.0,
                         "tree_canopy_pct": components.tree_canopy_pct or 0.0,
                         "water_pct": (sat or {}).get("water_pct", 0.0), "confidence": "n/a",
                         "osm_feature_count": 0, "radius_m": 250.0},
                "categories": categories,
            }
            if provider.name == "open_data":
                snap = provider._snapshot(loc, req.analysis_date, req.analysis_hour)
                ctx["land"] = snap["land"]
            hi_result = provider.report(ctx, str(OUTPUTS_DIR))
            pdf_path = Path(hi_result["pdf_path"])
            hi_info.pdf_available = True
            hi_info.pdf_relative_path = pdf_path.name
            if hi_result.get("used_qwen"):
                trace.add(f"[{loc.name}] Briefing narrative written by Qwen (Alibaba Cloud Model Studio).")
            trace.add(f"[{loc.name}] Deep investigation complete — report saved.")
        except providers.ProviderUnavailable as exc:
            trace.add(f"[{loc.name}] Heat Intelligence report unavailable ({exc}); proceeding with available signals only.")
    elif run_hi and used_demo:
        trace.add(f"[{loc.name}] Heat Intelligence would run in live mode; skipped under Demo Mode.")

    recommended_action = action_plan[0].action if action_plan else "Continue monitoring."

    return LocationResult(
        name=loc.name,
        latitude=loc.latitude,
        longitude=loc.longitude,
        temperature_c=round(temperature_c, 1),
        temperature_f=round(celsius_to_fahrenheit(temperature_c), 1),
        risk_score=risk.score,
        risk_level=risk.level,
        primary_driver=driver,
        recommended_action=recommended_action,
        evidence=evidence,
        work_windows=work_windows,
        action_plan=action_plan,
        heat_intelligence=hi_info,
        solar_ghi=env.get("solar_ghi"),
        solar_dni=env.get("solar_dni"),
        solar_dhi=env.get("solar_dhi"),
        tree_canopy_pct=components.tree_canopy_pct,
        impervious_pct=components.impervious_pct,
        data_source=data_source,
    )


def _ai_briefing(results: list[LocationResult], req: AnalyzeRequest) -> str | None:
    """Optional Qwen briefing. Explains the already-computed ranking; never changes it."""
    if not qwen_service.is_configured():
        return None
    lines = "; ".join(
        f"{r.name}: score {r.risk_score} ({r.risk_level}), {r.temperature_c}°C, driver: {r.primary_driver}"
        for r in results
    )
    return qwen_service.ask(
        "In about 80 words, brief a site supervisor on which site to use and why, and the one thing to do "
        f"first. Sites are already ranked best-first. Date {req.analysis_date}. Data: {lines}",
        max_tokens=300,
    )


def run_analysis(req: AnalyzeRequest) -> AnalyzeResponse:
    trace = _Trace()
    trace.add("Agent initialized. Received request for "
               f"{len(req.locations)} location(s), analysis date {req.analysis_date.isoformat()}.")

    provider = None
    if not req.demo_mode:
        try:
            provider = providers.get_provider()
            trace.add(f"Data provider ready: {provider.label}.")
        except providers.ProviderUnavailable as exc:
            trace.add(f"No live data provider ({exc}); entire analysis will run in Demo Mode.")

    # Run each location's full pipeline concurrently: each makes several network
    # calls, so sequential runs would take N times as long. Threads are fine
    # because the work is I/O-bound.
    with ThreadPoolExecutor(max_workers=max(1, len(req.locations))) as pool:
        futures = [pool.submit(_analyze_one_location, loc, req, provider, trace) for loc in req.locations]
        results = [f.result() for f in futures]

    results_sorted = sorted(results, key=lambda r: r.risk_score)
    preferred = results_sorted[0]

    if len(results) > 1:
        trace.add(
            f"Compared {len(results)} locations by Operational Risk Score. "
            f"Ranked '{preferred.name}' as preferred (score {preferred.risk_score})."
        )
        decision_summary = (
            f"HeatWise selected {preferred.name} because it shows the lowest combined "
            f"heat exposure and environmental risk among the {len(results)} sites analyzed. "
            f"Main driver: {preferred.primary_driver}."
        )
    else:
        decision_summary = (
            f"{preferred.name} carries {preferred.risk_level.lower()} operational heat risk "
            f"(score {preferred.risk_score}). Main driver: {preferred.primary_driver}."
        )

    trace.add("Generated autonomous action plan(s) and recommended work windows for all sites.")

    # Demo only if the user asked for it OR every site ended up on bundled data.
    demo_mode_effective = req.demo_mode or all(r.data_source == "demo" for r in results)

    briefing = None
    if not demo_mode_effective:
        briefing = _ai_briefing(results_sorted, req)
        if briefing:
            trace.add("Supervisor briefing written by Qwen (Alibaba Cloud Model Studio) from the computed ranking.")

    return AnalyzeResponse(
        request_id=str(uuid.uuid4()),
        generated_at=datetime.now(timezone.utc).isoformat(),
        demo_mode=demo_mode_effective,
        preferred_site=preferred.name,
        decision_summary=decision_summary,
        results=results_sorted,
        decision_trace=trace.as_list(),
        data_provider="Demo data" if demo_mode_effective else (provider.label if provider else "Demo data"),
        ai_briefing=briefing,
    )
