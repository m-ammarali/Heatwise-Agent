import type { ActionPlanItem } from "../types/api";
import { RISK } from "../lib/risk";
import { ChevronDown } from "./icons";

const MAP: Record<ActionPlanItem["priority"], keyof typeof RISK> = {
  LOW: "LOW",
  MEDIUM: "MODERATE",
  HIGH: "HIGH",
  CRITICAL: "CRITICAL",
};

export default function ActionPlanList({ items }: { items: ActionPlanItem[] }) {
  return (
    <div className="rounded-lg border border-line bg-white p-6 h-full">
      <h3 className="text-sm font-semibold text-ink">Action plan</h3>
      <ol className="mt-4 space-y-5">
        {items.map((a, i) => {
          const c = RISK[MAP[a.priority]];
          return (
            <li key={i} className="flex gap-3">
              <span
                className="mt-0.5 w-6 h-6 shrink-0 rounded-full text-xs font-bold flex items-center justify-center"
                style={{ background: c.bg, color: c.text, border: `1px solid ${c.border}` }}
              >
                {i + 1}
              </span>
              <div className="min-w-0">
                <p className="text-[15px] font-semibold leading-snug">{a.action}</p>
                <p className="mt-1 text-sm text-ink-2 leading-relaxed">{a.reason}</p>
                <details className="group mt-2">
                  <summary className="inline-flex items-center gap-1 cursor-pointer text-xs font-medium text-brand hover:text-brand-dark list-none">
                    Evidence behind this
                    <ChevronDown className="w-3.5 h-3.5 transition-transform group-open:rotate-180" />
                  </summary>
                  <ul className="mt-2 space-y-1.5 text-xs text-ink-2 leading-relaxed list-disc pl-4">
                    {a.supporting_data.map((s, j) => <li key={j}>{s}</li>)}
                  </ul>
                </details>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
