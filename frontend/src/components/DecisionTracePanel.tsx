import type { DecisionTraceStep, HeatIntelligenceInfo } from "../types/api";
import { ChevronDown, DownloadIcon } from "./icons";

export function DecisionTracePanel({ trace }: { trace: DecisionTraceStep[] }) {
  return (
    <details className="group rounded-lg border border-line bg-white">
      <summary className="flex items-center justify-between cursor-pointer list-none px-6 py-4">
        <div>
          <h3 className="text-sm font-semibold text-ink">Decision trace</h3>
          <p className="text-xs text-ink-3 mt-0.5">Every step the agent took, in order. {trace.length} steps.</p>
        </div>
        <ChevronDown className="w-5 h-5 text-ink-3 transition-transform group-open:rotate-180" />
      </summary>
      <ol className="border-t border-line px-6 py-4 space-y-2 max-h-[420px] overflow-y-auto">
        {trace.map((t) => (
          <li key={t.step} className="flex gap-3 text-sm leading-relaxed">
            <span className="w-6 shrink-0 text-right text-ink-3 tnum">{t.step}.</span>
            <span className="text-ink-2">{t.description}</span>
          </li>
        ))}
      </ol>
    </details>
  );
}

export function HeatIntelligenceBadge({ info }: { info: HeatIntelligenceInfo }) {
  if (!info.requested) {
    return (
      <div className="rounded-lg border border-line bg-soft px-6 py-4 flex gap-3 items-start">
        <span className="mt-1.5 w-2 h-2 rounded-full bg-ink-3 shrink-0" />
        <p className="text-sm text-ink-2 leading-relaxed">
          <span className="font-semibold text-ink">Deep investigation skipped. </span>
          {info.reason}
        </p>
      </div>
    );
  }
  return (
    <div className="rounded-lg border border-line bg-white px-6 py-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div className="flex gap-3 items-start">
        <span className="mt-1.5 w-2 h-2 rounded-full bg-accent shrink-0" />
        <div>
          <p className="text-sm font-semibold text-ink">
            {info.pdf_available ? "Heat Intelligence brief ready" : "Deep investigation requested"}
          </p>
          <p className="text-sm text-ink-2 mt-0.5 leading-relaxed">{info.reason}</p>
          {info.categories.length > 0 && (
            <p className="mt-2 flex flex-wrap gap-1.5">
              {info.categories.map((c) => (
                <span key={c} className="rounded bg-soft border border-line px-2 py-0.5 text-xs text-ink-2 capitalize">{c}</span>
              ))}
            </p>
          )}
        </div>
      </div>
      {info.pdf_available && info.pdf_relative_path && (
        <a
          href={`/api/reports/${info.pdf_relative_path}`}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 inline-flex items-center justify-center gap-2 rounded-md bg-brand hover:bg-brand-dark text-white text-sm font-semibold px-4 py-2.5 transition-colors"
        >
          <DownloadIcon /> Open PDF brief
        </a>
      )}
    </div>
  );
}
