import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { HistoryEntry } from "../types/api";
import { levelFromScore } from "../lib/risk";
import RiskChip from "../components/RiskChip";

export default function History() {
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getHistory().then(setEntries).catch((e) => setError(e instanceof Error ? e.message : "Failed to load history."));
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 md:py-14">
      <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">History</h1>
      <p className="mt-2 text-ink-2">Every analysis is stored on this machine.</p>

      {error && <p className="mt-6 text-sm text-[#a3263c]">{error}</p>}

      {entries && entries.length === 0 && (
        <div className="mt-8 rounded-lg border border-line bg-soft p-10 text-sm text-ink-2">
          Nothing here yet. <Link to="/dashboard" className="font-medium text-brand hover:text-brand-dark">Run an analysis</Link> and it will appear in this list.
        </div>
      )}

      {entries && entries.length > 0 && (
        <div className="mt-8 rounded-lg border border-line bg-white overflow-hidden">
          {entries.map((e) => (
            <div key={e.request_id} className="flex items-center justify-between gap-4 px-6 py-4 border-b border-line last:border-0">
              <div className="min-w-0">
                <p className="font-medium text-[15px] truncate">{e.preferred_site}</p>
                <p className="text-xs text-ink-3 mt-0.5 tnum">
                  {new Date(e.generated_at).toLocaleString()} · {e.location_names.length} site{e.location_names.length > 1 ? "s" : ""}
                  {e.demo_mode && " · demo data"}
                </p>
                <p className="text-xs text-ink-3 mt-0.5 truncate">{e.location_names.join(", ")}</p>
              </div>
              <div className="shrink-0 flex items-center gap-2">
                <span className="text-sm text-ink-2 tnum">worst {e.max_risk_score}</span>
                <RiskChip level={levelFromScore(e.max_risk_score)} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
