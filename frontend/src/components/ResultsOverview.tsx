import type { LocationResult } from "../types/api";
import { RISK, sourceLabel } from "../lib/risk";
import { ThermalScale } from "./ThermalScale";
import RiskChip from "./RiskChip";

export function DecisionHero({ result, siteCount, summary }: { result: LocationResult; siteCount: number; summary: string }) {
  const c = RISK[result.risk_level];
  return (
    <div className="rounded-lg border border-line bg-white shadow-card overflow-hidden flex">
      <div className="w-1.5 shrink-0" style={{ background: c.solid }} />
      <div className="p-6 md:p-7 flex-1 md:flex md:items-center md:justify-between gap-8">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold tracking-wider text-ink-3 uppercase">
            {siteCount > 1 ? "Recommended site" : "Result"}
          </p>
          <h2 className="mt-1 text-2xl md:text-3xl font-semibold tracking-tight">{result.name}</h2>
          <p className="mt-2 text-[15px] leading-relaxed text-ink-2">{summary}</p>
        </div>
        <div className="mt-5 md:mt-0 shrink-0 flex items-baseline gap-3">
          <span className="text-5xl font-semibold tnum tracking-tight">{result.risk_score}</span>
          <div>
            <p className="text-xs text-ink-3">out of 100</p>
            <RiskChip level={result.risk_level} className="mt-1" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function RiskScoreCard({ result }: { result: LocationResult }) {
  const facts: [string, string][] = [
    ["Site temperature", `${result.temperature_c.toFixed(1)} °C  (${result.temperature_f.toFixed(0)} °F)`],
    ["Solar irradiance", result.solar_ghi != null ? `${Math.round(result.solar_ghi)} W/m²` : "n/a"],
    ["Paved / built-up", result.impervious_pct != null ? `${result.impervious_pct.toFixed(0)} %` : "n/a"],
    ["Vegetation", result.tree_canopy_pct != null ? `${result.tree_canopy_pct.toFixed(0)} %` : "n/a"],
  ];
  return (
    <div className="rounded-lg border border-line bg-white p-6 h-full">
      <div className="flex items-start justify-between">
        <h3 className="text-sm font-semibold text-ink">Operational risk score</h3>
        <RiskChip level={result.risk_level} />
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-6xl font-semibold tnum tracking-tight">{result.risk_score}</span>
        <span className="text-base text-ink-3">/ 100</span>
      </div>
      <div className="mt-4">
        <ThermalScale score={result.risk_score} size="lg" showLabels />
      </div>
      <dl className="mt-6 grid grid-cols-2 gap-x-6 gap-y-4 border-t border-line pt-5">
        {facts.map(([k, v]) => (
          <div key={k}>
            <dt className="text-xs text-ink-3">{k}</dt>
            <dd className="mt-0.5 text-[15px] font-medium tnum">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-5 text-xs text-ink-3">
        {sourceLabel(result.data_source)}
        {result.data_source === "open_data" && " · site temperature includes a modelled land-cover adjustment"}
      </p>
    </div>
  );
}

export function ComparisonTable({
  results,
  selectedIdx,
  onSelect,
}: {
  results: LocationResult[];
  selectedIdx: number;
  onSelect: (i: number) => void;
}) {
  return (
    <div className="rounded-lg border border-line bg-white overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[720px]">
          <thead>
            <tr className="bg-soft text-left text-xs font-semibold uppercase tracking-wider text-ink-3">
              <th className="px-5 py-3 w-12">#</th>
              <th className="px-3 py-3">Site</th>
              <th className="px-3 py-3 w-56">Risk score</th>
              <th className="px-3 py-3">Main driver</th>
              <th className="px-3 py-3">Recommended action</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr
                key={r.name}
                onClick={() => onSelect(i)}
                className={`border-t border-line cursor-pointer transition-colors ${
                  selectedIdx === i ? "bg-brand-soft/60" : "hover:bg-soft"
                }`}
              >
                <td className="px-5 py-4 align-top">
                  <span
                    className="inline-flex w-6 h-6 items-center justify-center rounded-full text-xs font-bold text-white"
                    style={{ background: RISK[r.risk_level].solid }}
                  >
                    {i + 1}
                  </span>
                </td>
                <td className="px-3 py-4 align-top font-medium text-[15px]">{r.name}</td>
                <td className="px-3 py-4 align-top">
                  <div className="flex items-center gap-3">
                    <span className="w-7 text-right font-semibold tnum">{r.risk_score}</span>
                    <div className="flex-1 min-w-[80px]"><ThermalScale score={r.risk_score} /></div>
                    <RiskChip level={r.risk_level} />
                  </div>
                </td>
                <td className="px-3 py-4 align-top text-ink-2 max-w-[220px]">{r.primary_driver}</td>
                <td className="px-3 py-4 align-top text-ink-2 max-w-[280px]">{r.recommended_action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
