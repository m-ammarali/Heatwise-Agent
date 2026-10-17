# API_USAGE

Detailed mapping of every FortyGuard capability HeatWise calls, sourced
directly from the official quickstart repo
(`FortyGuard-Tech/temperature-api-quickstart`) — no invented endpoints or
fields.

## Client

`backend/fortyguard/client.py` is the vendored, **unmodified**
`FortyGuardClient` from the official quickstart. HeatWise never
re-implements FortyGuard request/response handling itself; it only calls
the client's public methods.

## 1. Temperature / Heatmap — `create_heatmap()`

- **Endpoint:** `POST /v1/heatmap` (async submit → poll)
- **Called from:** `services/fortyguard_service.py::get_site_temperature_c`
- **Request:** a small square `polygon_aoi` GeoJSON built around each
  site's lat/lon (`services/geo.py::square_polygon_aoi`), `start_date`,
  `start_time`, `filter_type=1` (single-hour snapshot), `granularity=60`,
  `analytic_type="tcm"`
- **Response fields used:** `result.stats_data.Temperature_stats.mean`
  (falls back to averaging `result.map_data.features[].properties.temperature`
  tile-by-tile if stats aren't present)
- **Why a polygon for a point-based product:** HeatWise's sites are work
  locations, not property parcels, but `create_heatmap` requires a
  polygon AOI — the same pattern the quickstart's own parcel-analysis
  notebooks use. A small buffer keeps the call cheap and the result
  representative of the specific site.

## 2. Environmental Parameters — `environmental_parameters()`

- **Endpoint:** `POST /v1/env_params`
- **Called from:** `get_environmental_parameters`
- **Request:** `latitude`, `longitude`, `temperature` (the *real* value
  returned by step 1 — never hardcoded), `start_date`, `start_time`
- **Response fields used:** `result.locations[0].parameters.heat_index_celsius`,
  `.apparent_temperature_celsius`, `.wet_bulb_temperature_celsius`,
  `.relative_humidity_percent`; `result.locations[0].solar_irradiance.clear_sky.{ghi,dni,dhi}`

## 3. Satellite Segmentation — `satellite_segmentation()` (Premium)

- **Endpoint:** `POST /v1/satellite`
- **Called from:** `get_satellite_context`
- **Response fields used:** `result.segmentation.segments` (a class→percent
  map) — HeatWise sums tree/grass/plant-labeled classes into
  `tree_canopy_pct` and building/road/pavement-labeled classes into
  `impervious_pct`, both of which feed the risk engine directly

## 4. Street View Segmentation — `street_view_segmentation()` (Premium)

- **Endpoint:** `POST /v1/streetview`
- **Called from:** `get_street_context`
- **Response fields used:** `result.front.segments` — sky-openness and
  street-level tree coverage, retrieved as additional ground-truth context

## 5. Heat Intelligence — `heat_intelligence()` (Premium)

- **Endpoint:** `POST /v1/heat_intelligence`
- **Called from:** `generate_heat_intelligence_report`
- **Conditional call:** only invoked when the HeatWise Risk Score is
  HIGH/CRITICAL or the user forces deep investigation
  (`agent/decision_engine.py::should_run_heat_intelligence`)
- **Request:** `latitude`, `longitude`, `temperature` (real, from step 1),
  `date`, `analysis` (category list — `geographic`/`environmental`/`urban`
  always; `+events`/`+anthropogenic` when force-requested)
- **Response:** unlike the others, this returns a **PDF file path**, not
  JSON — served back to the frontend via `/api/reports/{filename}`

## Credit-conscious orchestration

`should_run_heat_intelligence()` is the single decision point that keeps
HeatWise from burning API credits on low-risk sites — it's called once
per site, after the risk score is already computed from the cheaper
endpoints, and its output (and reasoning) is shown directly in the
Decision Trace panel.
