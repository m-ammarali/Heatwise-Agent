import { RISK, levelFromScore } from "../lib/risk";

interface Props {
  score: number; // 0-100
  size?: "sm" | "lg";
  showLabels?: boolean;
}

/** A plain horizontal scale: four risk bands, filled up to the score. */
export function ThermalScale({ score, size = "sm", showLabels = false }: Props) {
  const s = Math.max(0, Math.min(100, score));
  const color = RISK[levelFromScore(s)].solid;
  const h = size === "lg" ? "h-3" : "h-2";
  return (
    <div className="w-full">
      <div className={`relative ${h} w-full rounded-full bg-line overflow-hidden`}>
        <div className="absolute inset-y-0 left-0 rounded-full" style={{ width: `${s}%`, background: color }} />
        {[25, 50, 75].map((t) => (
          <span key={t} className="absolute inset-y-0 w-px bg-white" style={{ left: `${t}%` }} />
        ))}
      </div>
      {showLabels && (
        <div className="mt-1.5 grid grid-cols-4 text-[11px] text-ink-3">
          <span>Low</span>
          <span>Moderate</span>
          <span>High</span>
          <span className="text-right">Critical</span>
        </div>
      )}
    </div>
  );
}
