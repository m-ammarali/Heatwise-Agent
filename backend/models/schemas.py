"""Pydantic models shared across the HeatWise Agent backend.

These describe HeatWise's OWN request/response contracts (frontend <-> backend).
They are independent of any data provider's payload shapes (Open-Meteo,
OpenStreetMap, FortyGuard).
"""
from __future__ import annotations

from datetime import date as date_type
from typing import Literal, Optional

from pydantic import BaseModel, Field

RiskLevel = Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]


class LocationIn(BaseModel):
    """A single candidate site submitted by the user."""

    name: str = Field(..., min_length=1, max_length=120)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class AnalyzeRequest(BaseModel):
    locations: list[LocationIn] = Field(..., min_length=1, max_length=5)
    analysis_date: date_type
    analysis_hour: str = Field(
        default="14:00",
        description="HH:MM, 24h. Defaults to design-peak afternoon (2 PM local).",
    )
    deep_investigation: bool = Field(
        default=False,
        description="If true, always run the full Heat Intelligence report "
        "regardless of computed risk level.",
    )
    demo_mode: bool = Field(default=False)


class EvidenceSignal(BaseModel):
    label: str
    direction: Literal["up", "down", "neutral"]
    detail: str


class WorkWindow(BaseModel):
    label: Literal["BEST", "CAUTION", "AVOID", "RECOVERY"]
    start: str
    end: str
    note: str


class ActionPlanItem(BaseModel):
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    action: str
    reason: str
    supporting_data: list[str]


class HeatIntelligenceInfo(BaseModel):
    requested: bool
    categories: list[str] = Field(default_factory=list)
    reason: str
    pdf_available: bool = False
    pdf_relative_path: Optional[str] = None


class LocationResult(BaseModel):
    name: str
    latitude: float
    longitude: float

    temperature_c: float
    temperature_f: float
    risk_score: int
    risk_level: RiskLevel

    primary_driver: str
    recommended_action: str

    evidence: list[EvidenceSignal]
    work_windows: list[WorkWindow]
    action_plan: list[ActionPlanItem]
    heat_intelligence: HeatIntelligenceInfo

    solar_ghi: Optional[float] = None
    solar_dni: Optional[float] = None
    solar_dhi: Optional[float] = None
    tree_canopy_pct: Optional[float] = None
    impervious_pct: Optional[float] = None

    data_source: Literal["live", "open_data", "demo"] = "live"


class DecisionTraceStep(BaseModel):
    step: int
    description: str


class AnalyzeResponse(BaseModel):
    request_id: str
    generated_at: str
    demo_mode: bool
    preferred_site: str
    decision_summary: str
    results: list[LocationResult]
    decision_trace: list[DecisionTraceStep]
    data_provider: str = ""
    ai_briefing: Optional[str] = None


class HistoryEntry(BaseModel):
    request_id: str
    generated_at: str
    demo_mode: bool
    preferred_site: str
    location_names: list[str]
    max_risk_score: int
