"""Minimal SQLite storage for analysis history."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from models.schemas import AnalyzeResponse, HistoryEntry

DB_PATH = Path(__file__).resolve().parent.parent / "heatwise.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    request_id TEXT PRIMARY KEY,
    generated_at TEXT NOT NULL,
    demo_mode INTEGER NOT NULL,
    preferred_site TEXT NOT NULL,
    location_names TEXT NOT NULL,
    max_risk_score INTEGER NOT NULL,
    payload TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(_SCHEMA)
    return conn


def save_analysis(response: AnalyzeResponse) -> None:
    conn = get_connection()
    try:
        max_score = max((r.risk_score for r in response.results), default=0)
        conn.execute(
            "INSERT OR REPLACE INTO analyses "
            "(request_id, generated_at, demo_mode, preferred_site, location_names, max_risk_score, payload) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                response.request_id,
                response.generated_at,
                int(response.demo_mode),
                response.preferred_site,
                json.dumps([r.name for r in response.results]),
                max_score,
                response.model_dump_json(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def list_history(limit: int = 50) -> list[HistoryEntry]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT request_id, generated_at, demo_mode, preferred_site, location_names, max_risk_score "
            "FROM analyses ORDER BY generated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        conn.close()

    return [
        HistoryEntry(
            request_id=row[0],
            generated_at=row[1],
            demo_mode=bool(row[2]),
            preferred_site=row[3],
            location_names=json.loads(row[4]),
            max_risk_score=row[5],
        )
        for row in rows
    ]


def get_analysis(request_id: str) -> Optional[AnalyzeResponse]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT payload FROM analyses WHERE request_id = ?", (request_id,)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return AnalyzeResponse.model_validate_json(row[0])
