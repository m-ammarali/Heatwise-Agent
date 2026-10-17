"""Locally generated 'Heat Intelligence Brief' PDF (free replacement for the
paid FortyGuard /v1/heat_intelligence report)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from services import qwen_service

ATTRIBUTION = ("Data: Open-Meteo.com (CC BY 4.0) and (c) OpenStreetMap contributors (ODbL). "
               "Microclimate adjustment is a modelled estimate, not a sensor measurement. "
               "HeatWise is an operational decision aid, not medical or occupational-safety advice.")


def _fallback_narrative(ctx: dict[str, Any]) -> str:
    cats = ", ".join(ctx["categories"]) or "overall"
    return (f"{ctx['name']} scores {ctx['risk_score']}/100 ({ctx['risk_level']}). The main driver is "
            f"{ctx['primary_driver'].lower()}. This brief examines the {cats} factors behind that score "
            "so the action plan below can be traced back to specific signals.")


def generate_heat_brief(ctx: dict[str, Any], output_dir: str) -> dict[str, Any]:
    """ctx keys: name, latitude, longitude, analysis_date, analysis_hour, temperature_c, raw_air_temperature_c,
    adjustment_c, risk_score, risk_level, primary_driver, breakdown, weights, evidence[(label,dir,detail)],
    work_windows[(label,start,end,note)], action_plan[(priority,action,reason)], land, categories."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"heat_intelligence_{uuid.uuid4()}.pdf"

    narrative = None
    if qwen_service.is_configured():
        facts = (f"Site: {ctx['name']} ({ctx['latitude']:.4f}, {ctx['longitude']:.4f}); date {ctx['analysis_date']} "
                 f"{ctx['analysis_hour']}. Risk {ctx['risk_score']}/100 {ctx['risk_level']}. "
                 f"Site temp {ctx['temperature_c']} C (regional air temp {ctx['raw_air_temperature_c']} C, "
                 f"modelled microclimate adjustment {ctx['adjustment_c']:+} C). "
                 f"Land cover within {ctx['land']['radius_m']:.0f} m: impervious {ctx['land']['impervious_pct']}%, "
                 f"vegetation {ctx['land']['tree_canopy_pct']}%, water {ctx['land']['water_pct']}%. "
                 f"Primary driver: {ctx['primary_driver']}. Focus areas: {', '.join(ctx['categories'])}.")
        narrative = qwen_service.ask(
            "Write a 120-word supervisor briefing explaining why this site is risky and what to do first.\n" + facts)
    used_qwen = narrative is not None
    narrative = narrative or _fallback_narrative(ctx)

    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=20, textColor=colors.HexColor("#b45309"))
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, textColor=colors.HexColor("#1f2937"), spaceBefore=10)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.5, leading=13)
    small = ParagraphStyle("s", parent=body, fontSize=7.5, textColor=colors.HexColor("#6b7280"))

    def tbl(rows, widths, header=True):
        t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
        style = [("FONTSIZE", (0, 0), (-1, -1), 8.5), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                 ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")])]
        if header:
            style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef3c7"))]
        t.setStyle(TableStyle(style))
        return t

    P = lambda s, st=body: Paragraph(escape(str(s).replace('²', '2')), st)   # noqa: E731
    story = [
        P("HeatWise Heat Intelligence Brief", h1),
        P(f"{ctx['name']}  |  {ctx['latitude']:.4f}, {ctx['longitude']:.4f}  |  {ctx['analysis_date']} {ctx['analysis_hour']}", body),
        P(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  |  Narrative: "
          f"{'Qwen (Alibaba Cloud Model Studio)' if used_qwen else 'rule-based'}", small),
        Spacer(1, 6), P("Summary", h2), P(narrative),
        P("Operational Risk Score", h2),
        tbl([["Score", "Level", "Primary driver"],
             [f"{ctx['risk_score']} / 100", ctx["risk_level"], ctx["primary_driver"]]], [30 * mm, 30 * mm, 110 * mm]),
        P("Score breakdown (weighted, auditable)", h2),
        tbl([["Component", "Sub-score (0-100)", "Weight", "Contribution"]] +
            [[k.replace("_", " ").title(), f"{ctx['breakdown'][k]:.0f}", f"{ctx['weights'][k] * 100:.0f}%",
              f"{ctx['breakdown'][k] * ctx['weights'][k]:.1f}"] for k in ctx["weights"]],
            [60 * mm, 40 * mm, 30 * mm, 40 * mm]),
        P("Site conditions", h2),
        tbl([["Metric", "Value"],
             ["Regional air temperature (Open-Meteo model)", f"{ctx['raw_air_temperature_c']:.1f} C"],
             ["Microclimate adjustment (land-cover model)", f"{ctx['adjustment_c']:+.1f} C"],
             ["Site temperature used in score", f"{ctx['temperature_c']:.1f} C"],
             [f"Impervious surface (within {ctx['land']['radius_m']:.0f} m)", f"{ctx['land']['impervious_pct']}%"],
             ["Vegetation cover", f"{ctx['land']['tree_canopy_pct']}%"],
             ["Water", f"{ctx['land']['water_pct']}%"],
             ["Land-cover data confidence", f"{ctx['land']['confidence']} ({ctx['land']['osm_feature_count']} OSM features)"]],
            [100 * mm, 70 * mm]),
        P("Evidence", h2),
        tbl([["Signal", "Effect", "Detail"]] + [[l, d, t] for l, d, t in ctx["evidence"]],
            [45 * mm, 18 * mm, 107 * mm]),
        P("Work-window timeline", h2),
        tbl([["Window", "From", "To", "Note"]] + [[l, s, e, n] for l, s, e, n in ctx["work_windows"]],
            [25 * mm, 18 * mm, 18 * mm, 109 * mm]),
        P("Action plan", h2),
        tbl([["Priority", "Action", "Why"]] + [[p, a, r] for p, a, r in ctx["action_plan"]],
            [22 * mm, 80 * mm, 68 * mm]),
        Spacer(1, 10), P(ATTRIBUTION, small),
    ]
    # Paragraph-wrap long cells in tables
    for fl in story:
        if isinstance(fl, Table):
            for r, row in enumerate(fl._cellvalues):
                fl._cellvalues[r] = [Paragraph(escape(str(c).replace('²', '2')), body if r else ParagraphStyle("th", parent=body, fontName="Helvetica-Bold"))
                                     if not isinstance(c, Paragraph) else c for c in row]
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=16 * mm, bottomMargin=16 * mm,
                      title=f"HeatWise Brief - {ctx['name']}").build(story)
    return {"pdf_path": str(path), "used_qwen": used_qwen}
