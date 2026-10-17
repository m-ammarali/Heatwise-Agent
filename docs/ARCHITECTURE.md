# ARCHITECTURE

## Layers

```
frontend/   React + TypeScript + Vite + Tailwind — dashboard, results UI
backend/main.py   FastAPI routes (/api/analyze, /api/status, /api/history, /api/reports)
backend/agent/     Orchestrator, risk engine, decision engine, demo data
backend/services/  FortyGuard service wrapper + geo helpers
backend/fortyguard/  Vendored, unmodified official FortyGuard client
backend/models/    Pydantic request/response schemas
backend/database/  SQLite history storage
```

## Request lifecycle

1. Frontend POSTs `AnalyzeRequest` (1–5 `LocationIn`, analysis date/hour,
   flags) to `/api/analyze`.
2. `agent/orchestrator.py::run_analysis` authenticates the FortyGuard
   client once (or determines Demo Mode applies globally), then processes
   each location independently through `_analyze_one_location`.
3. Per location:
   - **OBSERVE**: `create_heatmap` → real temperature (°C)
   - **ANALYZE**: `environmental_parameters` (solar/heat-index) and
     `satellite_segmentation` (canopy/impervious) → `RiskComponents`
   - Risk scoring: `agent/risk_scoring.py::calculate_heat_risk` — a
     weighted, clamped, fully transparent 0–100 score with a visible
     per-factor breakdown
   - Evidence: `agent/decision_engine.py::build_evidence` turns the same
     components into human-readable up/down/neutral signals
   - **INVESTIGATE**: `should_run_heat_intelligence` decides whether to
     call the expensive `heat_intelligence` endpoint, and with which
     analysis categories
   - **DECIDE/ACT**: `recommend_safe_work_window` and
     `generate_action_plan` produce the timeline and prioritized actions
   - Any live-call failure at any step triggers a **per-location** fallback
     to Demo Mode data (`agent/demo_data.py`), logged explicitly in the
     decision trace and reflected in that location's `data_source` field
4. Results are sorted by risk score (ascending = safest first); the top
   site becomes `preferred_site`.
5. The full response is persisted to SQLite (`database/db.py`) and
   returned to the frontend.

## Why a custom state-machine instead of a heavier agent framework

The workflow is a fixed five-stage pipeline with one genuine branch point
(the Heat Intelligence tool-selection decision). A plain, testable Python
function chain (`orchestrator.py`) makes that branch point explicit and
keeps every step unit-testable in isolation — see `backend/tests/`.

## Data integrity guarantees

- `FORTYGUARD_API_KEY` is read only in `services/fortyguard_service.py`
  from environment variables; it is never included in any response model,
  logged, or reachable from the frontend.
- The risk-scoring pipeline never accepts a hardcoded temperature — every
  call to `environmental_parameters` and `heat_intelligence` is fed the
  temperature actually returned by `create_heatmap` (or the demo dataset's
  matching value) for that specific site.
- Demo fallback is always explicit: each `LocationResult.data_source` is
  `"live"` or `"demo"`, and the orchestrator logs the fallback reason into
  the decision trace rather than silently swapping data sources.
