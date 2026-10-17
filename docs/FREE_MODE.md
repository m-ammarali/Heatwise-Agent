# HeatWise Free Mode (no FortyGuard key needed)

The FortyGuard API was only available during their hackathon. HeatWise now has a **provider layer**
(`backend/services/providers.py`) so the whole agent - orchestrator, risk model, decision engine,
dashboard - runs unchanged on free data.

| Setting `DATA_PROVIDER` | Data source | Key needed |
|---|---|---|
| `open_data` (default) | Open-Meteo (weather, solar) + OpenStreetMap (land cover) | none |
| `fortyguard` | original FortyGuard API | yes (expired) |
| `demo` | bundled demo data, never touches the network | none |

## What replaced each FortyGuard endpoint

| FortyGuard endpoint | Free replacement | Honest difference |
|---|---|---|
| `/v1/heatmap` tile temperature | Open-Meteo hourly `temperature_2m` + **modelled microclimate adjustment** from land cover | Base temperature is a 1-11 km weather model, not 60 m tiles. The +/- adjustment (max 3.5 C) is an estimate. |
| `/v1/env_params` | Open-Meteo humidity, radiation (GHI/DNI/DHI) + NWS heat index + Stull wet-bulb (computed locally) | Equivalent signals; solar is actual (cloud-aware), not clear-sky. |
| `/v1/satellite` | OpenStreetMap buildings/roads/parks/trees/water within 250 m via Overpass | Map data, not imagery. Quality varies; a confidence level is reported per site. |
| `/v1/streetview` | not used by the agent's score | none |
| `/v1/heat_intelligence` PDF | Locally generated "Heat Intelligence Brief" PDF (reportlab), narrative optionally by **Qwen** | Same conditional trigger (HIGH/CRITICAL only). |

Also improved: work windows are now computed from the **real hourly forecast** (each hour scored with the
same risk model) instead of a fixed template; the US-only longitude check was removed; and a bug where
"Limited tree coverage" was tagged as risk-reducing was fixed.

## Run it (5 minutes)

```bash
# backend
cd backend
pip install -r requirements.txt
cp .env.example .env            # defaults are fine - no key needed
python check_setup.py           # verifies internet access to every source
python prewarm_cache.py         # night before: caches demo sites for offline resilience
python -m uvicorn main:app --port 8000

# open http://localhost:8000   (the built frontend is served by the backend)
```

Frontend development (optional): `cd frontend && npm install && npm run dev` -> http://localhost:5173.
Rebuild the UI after edits: `npm run build`.

Tests: `cd backend && python -m pytest -q` (31 tests, all network mocked).

## Optional: Qwen on Alibaba Cloud (fits the hackathon theme)

1. Activate Alibaba Cloud Model Studio and create an API key in the **Singapore (international)** region.
2. In `backend/.env` set `DASHSCOPE_API_KEY=...` and, if the default model name is rejected, set
   `QWEN_MODEL` to a current model ID from the console.
3. Re-run `python check_setup.py`. The dashboard then shows a "Supervisor briefing - written by Qwen" card
   and the PDF narrative is Qwen-written. Qwen only *explains* numbers HeatWise computed; it never sets the score.

New-user free quota existed at the time of writing (1M tokens per model, 90 days, Singapore region) -
confirm on your console, and use the "free quota only" setting to avoid charges.

## Failure ladder (why the demo will not die on stage)

1. Fresh live data -> 2. last cached copy of weather/land cover (labelled "stale") -> 3. clearly-labelled Demo Mode
(per site). Nothing is ever silently faked: every result shows its `data_source`.
Worst case, tick **Demo mode** or set `DATA_PROVIDER=demo`; the Lahore demo scenario still runs end to end.

## Licences / attribution (already in the UI footer)

* Open-Meteo: free for non-commercial use, CC BY 4.0, fair-use ~10,000 calls/day. Commercial use needs a paid plan.
* OpenStreetMap: (c) OpenStreetMap contributors, ODbL. Overpass public servers are shared - keep volume low.

## What to say on stage (accurate claims)

* "We replaced a paid tile-level API with open data. Weather comes from Open-Meteo; hyperlocal differences come from
  OpenStreetMap land cover within 250 m, converted to a bounded, documented microclimate adjustment."
* "Two sites in the same weather grid cell are separated by their surroundings - pavement vs. park - and every
  adjustment is shown in the evidence panel."
* Do NOT say "real tile-level measurements" or "satellite segmentation" - that was FortyGuard and no longer true.

Likely judge question: *"Is this validated?"* -> "The weights and the adjustment are transparent heuristics, not a
medical or calibrated model; validating against local sensor data is the next step."

## Slides / document edits needed

* Slide 1/9/10 and docx: remove "Powered by FortyGuard Temperature API".
* Slide 6 (architecture): replace the five FortyGuard endpoint boxes with **Open-Meteo** (weather/solar),
  **OpenStreetMap** (land cover), **Local PDF brief**, **Qwen (optional)**.
* Slide 7: "Credit-conscious by design" -> "Compute-conscious": the deep report/Qwen narrative runs only when risk is HIGH/CRITICAL.
* Slide 9: "FortyGuard Temperature API" card -> "Open data: Open-Meteo + OpenStreetMap".
