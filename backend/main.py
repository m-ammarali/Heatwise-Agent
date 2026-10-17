"""HeatWise Agent — FastAPI backend.

Never exposes any API key (FORTYGUARD_API_KEY, DASHSCOPE_API_KEY) to the
frontend, logs, or error messages.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parent / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("heatwise.main")

from agent.orchestrator import OUTPUTS_DIR, run_analysis  # noqa: E402
from database import db  # noqa: E402
from models.schemas import AnalyzeRequest, AnalyzeResponse, HistoryEntry  # noqa: E402
from services import providers, qwen_service  # noqa: E402

app = FastAPI(title="HeatWise Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StatusResponse(BaseModel):
    provider: str
    provider_label: str
    live_data_available: bool
    qwen_enabled: bool
    detail: str


@app.get("/api/status", response_model=StatusResponse)
def status() -> StatusResponse:
    """Which data provider is active. Never returns any API key."""
    name = providers.configured_provider_name()
    qwen = qwen_service.is_configured()
    try:
        p = providers.get_provider()
        return StatusResponse(provider=p.name, provider_label=p.label, live_data_available=True,
                              qwen_enabled=qwen, detail=f"Live data via {p.label}.")
    except providers.ProviderUnavailable as exc:
        return StatusResponse(provider=name, provider_label="Demo data", live_data_available=False,
                              qwen_enabled=qwen, detail=f"{exc} Demo Mode will be used.")


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        response = run_analysis(request)
    except Exception as exc:  # noqa: BLE001
        # Never leak raw stack traces / internals to the client.
        logger.exception("Analysis failed")
        raise HTTPException(status_code=500, detail="HeatWise Agent could not complete this analysis. Please try again.") from exc

    try:
        db.save_analysis(response)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to persist analysis history (non-fatal)")

    return response


@app.get("/api/history", response_model=list[HistoryEntry])
def history(limit: int = 50) -> list[HistoryEntry]:
    return db.list_history(limit=limit)


@app.get("/api/history/{request_id}", response_model=AnalyzeResponse)
def history_detail(request_id: str) -> AnalyzeResponse:
    result = db.get_analysis(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return result


@app.get("/api/reports/{filename}")
def get_report(filename: str) -> FileResponse:
    # Defend against path traversal; only serve files directly inside OUTPUTS_DIR.
    safe_name = Path(filename).name
    path = (OUTPUTS_DIR / safe_name).resolve()
    if not str(path).startswith(str(OUTPUTS_DIR.resolve())) or not path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(path, media_type="application/pdf", filename=safe_name)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

# --- Serve the built frontend (production) ---
# In local dev, Vite's own dev server handles the frontend and proxies /api/*
# here instead. In production there's no Vite dev server, so this same
# FastAPI process serves the built static files too — one deployable
# service, one URL, no CORS to configure between two separate hosts.
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback: serve the matching static file, or index.html for
        client-side routes (e.g. /dashboard, /history) so a direct link or
        page refresh doesn't 404. Registered last so it never shadows an
        /api/* route above it.
        """
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_FRONTEND_DIST / "index.html")
