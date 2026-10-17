import type { EvidenceSignal } from "../types/api";

const GROUPS: { dir: EvidenceSignal["direction"]; title: string; color: string; mark: string }[] = [
  { dir: "up", title: "Pushes the score up", color: "#a3263c", mark: "↑" },
  { dir: "down", title: "Pulls the score down", color: "#14724a", mark: "↓" },
  { dir: "neutral", title: "Context and data quality", color: "#475467", mark: "•" },
];

export default function EvidencePanel({ evidence }: { evidence: EvidenceSignal[] }) {
  return (
    <div className="rounded-lg border border-line bg-white p-6 h-full">
      <h3 className="text-sm font-semibold text-ink">Why this score</h3>
      <div className="mt-4 space-y-5">
        {GROUPS.map((g) => {
          const items = evidence.filter((e) => e.direction === g.dir);
          if (items.length === 0) return null;
          return (
            <div key={g.dir}>
              <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: g.color }}>
                {g.title}
              </p>
              <ul className="mt-2 space-y-3">
                {items.map((e) => (
                  <li key={e.label} className="flex gap-3">
                    <span className="mt-0.5 w-4 shrink-0 text-center font-bold" style={{ color: g.color }}>{g.mark}</span>
                    <div>
                      <p className="text-[15px] font-medium leading-snug">{e.label}</p>
                      <p className="mt-0.5 text-sm text-ink-2 leading-relaxed">{e.detail}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}
