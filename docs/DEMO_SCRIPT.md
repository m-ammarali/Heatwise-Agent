# DEMO_SCRIPT

Target length: 2–5 minutes.

## 1. Problem (20s)
"Outdoor teams plan around city-level weather. But heat doesn't work at
the city scale — a parking lot and a shaded park two blocks apart can
differ by several degrees. Generic forecasts can't tell a crew which site
is actually safer today."

## 2. Limitation (15s)
Show the Landing page. Point at the OBSERVE / REASON / ACT pillars.
"That's the gap HeatWise closes, using FortyGuard's hyperlocal Temperature
API."

## 3. Solution (20s)
Navigate to Dashboard. "HeatWise Agent takes up to five candidate sites and
autonomously investigates each one — real tile-level temperature, solar
exposure, land cover — then decides what to do about it."

## 4. Demo (60–90s)
- Click "Load Phoenix demo scenario" (or enter three real coordinates with
  a live API key).
- Click "⚡ Analyze with HeatWise Agent" — let the agent activity sequence
  play (OBSERVE → ANALYZE → INVESTIGATE steps visibly ticking off).
- Land on results: point at the preferred-site hero, the risk comparison
  table, and the thermal-scale risk score.
- Click between sites; show the Evidence panel ("WHY THIS DECISION?") and
  the Work Window timeline.

## 5. Agent action (30s)
Open the Decision Trace panel. "This is the agent's full audit trail —
every tool call and every decision it made, including *not* running the
expensive Heat Intelligence report on lower-risk sites to conserve
credits." Point at a HIGH/CRITICAL site's Heat Intelligence badge showing
the report *was* requested there.

## 6. Decision (15s)
Scroll back to the comparison table and the Action Plan panel. "The agent
doesn't just say it's hot — it tells you which site, which hours, and what
to do."

## 7. Impact (15s)
"Better operational decisions, grounded in real hyperlocal heat
intelligence — built entirely on FortyGuard's Temperature API."
