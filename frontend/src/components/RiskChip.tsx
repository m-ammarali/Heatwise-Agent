import type { RiskLevel } from "../types/api";
import { RISK } from "../lib/risk";

export default function RiskChip({ level, className = "" }: { level: RiskLevel; className?: string }) {
  const c = RISK[level];
  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold tracking-wide ${className}`}
      style={{ background: c.bg, color: c.text, border: `1px solid ${c.border}` }}
    >
      {level}
    </span>
  );
}
