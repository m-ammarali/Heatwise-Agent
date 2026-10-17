# PROJECT_SUMMARY

## What it is

HeatWise Agent is an autonomous AI agent that turns FortyGuard's hyperlocal
temperature intelligence into operational decisions for outdoor workforces:
which of several candidate sites is safest right now, when to schedule
high-exposure work, and what to do about it.

## Who it's for

Construction companies, delivery and logistics fleets, utility crews, city
operations teams, and event organizers — anyone deciding *where* and *when*
outdoor work happens during extreme heat.

## Why hyperlocal data matters

City-level weather can't distinguish a shaded park from an asphalt lot two
blocks away. FortyGuard's tile-level heatmap, solar, and land-cover data
lets HeatWise reason about the specific site, not the nearest airport.

## How the agent works

OBSERVE → ANALYZE → INVESTIGATE → DECIDE → ACT. See `ARCHITECTURE.md` for
the full diagram. The key autonomous decision: HeatWise's agent only
spends credits on the expensive Heat Intelligence report when the risk
score it already computed is HIGH or CRITICAL — an explicit, visible
tool-selection decision, not blanket API usage.

## What it decides autonomously

- A transparent 0–100 Operational Risk Score per site
- Which FortyGuard endpoints to call, and which Heat Intelligence
  analysis categories to request
- A ranked preference across up to 5 sites, with a stated reason
- A safe-work-window timeline (BEST / CAUTION / AVOID / RECOVERY)
- A prioritized action plan, each item citing the evidence behind it

## Why FortyGuard is essential

Every risk score, evidence signal, and recommendation traces back to a
real FortyGuard API response — temperature, solar irradiance, canopy
coverage, or the deep Heat Intelligence report. Without FortyGuard's
hyperlocal, tile-based data, HeatWise has nothing to reason over.

## Real-world impact and business potential

Extreme heat is a leading cause of preventable workplace injury and lost
productivity. A tool that turns temperature data into a defensible,
site-specific "work here, not there, and not right now" decision has
direct value for any organization with outdoor labor — and a natural
expansion path into OSHA heat-rule compliance reporting, insurance risk
assessment, and municipal outdoor-event permitting.
