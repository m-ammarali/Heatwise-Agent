"""HeatWise Operational Risk Score.

Explicitly NOT a medically certified heat-health index. This is a transparent,
weighted, explainable operational score (0-100) combining hyperlocal
temperature, thermal-comfort, solar, and environmental-context signals from
FortyGuard. Every component is visible so the score is auditable, not a
black box.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

RiskLevel = Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]

# OSHA's commonly cited "high heat" trigger is 80F / 26.7C for the heat index;
# we use the celsius-native NOAA/OSHA reference points the quickstart's own
# use-case notebooks cite (NOAA_EXTREME_C=32.0, OSHA_HIGH_C=32.2) as anchors,
# scaled into HeatWise's own 0-100 operational score.
TEMP_LOW_C = 27.0     # below this, temperature contributes ~0
TEMP_HIGH_C = 42.0    # at/above this, temperature contributes its full weight

HEAT_INDEX_LOW_C = 27.0
HEAT_INDEX_HIGH_C = 45.0

SOLAR_GHI_LOW = 200.0   # W/m^2, negligible direct solar stress
SOLAR_GHI_HIGH = 950.0  # W/m^2, near peak clear-sky summer irradiance

CANOPY_FULL_PROTECTION_PCT = 30.0  # tree canopy % at/above which shade is treated as strong


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _scale(value: Optional[float], low: float, high: float) -> float:
    """Linearly scale value into [0, 100], clamped. None -> 0 (no signal, no penalty).

    Defensive: if a non-numeric value slips through (e.g. an un-coerced list
    from an unexpected upstream response shape), treat it as no signal
    rather than raising, so one malformed field can't crash a whole
    analysis run.
    """
    if value is None:
        return 0.0
    if not isinstance(value, (int, float)):
        return 0.0
    if high == low:
        return 0.0
    return _clamp((value - low) / (high - low) * 100.0)


@dataclass
class RiskComponents:
    temperature_c: float
    heat_index_c: Optional[float] = None
    solar_ghi: Optional[float] = None
    tree_canopy_pct: Optional[float] = None
    impervious_pct: Optional[float] = None


@dataclass
class RiskResult:
    score: int
    level: RiskLevel
    breakdown: dict[str, float] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)


# Weights sum to 1.0. Temperature dominates; solar and built-environment
# context adjust it; vegetation context reduces it (protective factor).
WEIGHTS = {
    "temperature": 0.45,
    "heat_index": 0.20,
    "solar_exposure": 0.20,
    "impervious_surface": 0.10,
    "vegetation_protection": 0.05,  # protective: HIGHER canopy -> LOWER contribution
}


def calculate_heat_risk(components: RiskComponents) -> RiskResult:
    temp_score = _scale(components.temperature_c, TEMP_LOW_C, TEMP_HIGH_C)
    heat_index_score = _scale(components.heat_index_c, HEAT_INDEX_LOW_C, HEAT_INDEX_HIGH_C)
    solar_score = _scale(components.solar_ghi, SOLAR_GHI_LOW, SOLAR_GHI_HIGH)
    impervious_score = _scale(components.impervious_pct, 20.0, 90.0)

    # Vegetation is protective: more canopy -> less contribution to risk.
    canopy_pct = components.tree_canopy_pct if components.tree_canopy_pct is not None else 0.0
    vegetation_protection_score = _clamp(
        100.0 - _scale(canopy_pct, 0.0, CANOPY_FULL_PROTECTION_PCT)
    )

    breakdown = {
        "temperature": temp_score,
        "heat_index": heat_index_score,
        "solar_exposure": solar_score,
        "impervious_surface": impervious_score,
        "vegetation_protection": vegetation_protection_score,
    }

    weighted_total = sum(breakdown[k] * WEIGHTS[k] for k in WEIGHTS)
    score = int(round(_clamp(weighted_total)))

    if score >= 75:
        level: RiskLevel = "CRITICAL"
    elif score >= 50:
        level = "HIGH"
    elif score >= 25:
        level = "MODERATE"
    else:
        level = "LOW"

    return RiskResult(score=score, level=level, breakdown=breakdown, weights=dict(WEIGHTS))


def primary_driver(result: RiskResult, components: RiskComponents) -> str:
    """Plain-language explanation of the single largest contributor."""
    weighted = {k: result.breakdown[k] * WEIGHTS[k] for k in WEIGHTS}
    top_key = max(weighted, key=weighted.get)
    labels = {
        "temperature": f"High hyperlocal temperature ({components.temperature_c:.1f}°C)",
        "heat_index": "Elevated heat index / thermal comfort stress",
        "solar_exposure": "Strong direct solar irradiance",
        "impervious_surface": "High impervious surface coverage (urban heat retention)",
        "vegetation_protection": "Low tree canopy / limited shade protection",
    }
    return labels[top_key]