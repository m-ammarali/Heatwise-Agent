import { useEffect, useState } from "react";

const STEPS = [
  "Fetching hourly weather for each site",
  "Reading land cover around each pin",
  "Scoring heat risk and ranking the sites",
  "Building work windows from the hourly forecast",
  "Investigating the high-risk sites",
  "Writing the action plan",
];

export default function AgentActivityPanel() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (active >= STEPS.length - 1) return;
    const t = setTimeout(() => setActive((i) => i + 1), 1400);
    return () => clearTimeout(t);
  }, [active]);

  return (
    <div className="max-w-lg rounded-lg border border-line bg-white p-7 shadow-card">
      <div className="flex items-center gap-3">
        <span className="w-5 h-5 rounded-full border-2 border-line border-t-brand animate-spin" aria-hidden />
        <h2 className="text-base font-semibold">Analysing your sites</h2>
      </div>
      <p className="mt-1 text-sm text-ink-3">Public map servers can take up to half a minute on a first run.</p>
      <ul className="mt-6 space-y-3">
        {STEPS.map((s, i) => {
          const done = i < active;
          const current = i === active;
          return (
            <li key={s} className="flex items-center gap-3 text-[15px]">
              <span
                className={`w-5 h-5 shrink-0 rounded-full flex items-center justify-center text-[11px] font-bold ${
                  done ? "bg-brand text-white" : current ? "border-2 border-brand text-brand" : "border border-line-strong text-ink-3"
                }`}
              >
                {done ? "✓" : i + 1}
              </span>
              <span className={done ? "text-ink-2" : current ? "text-ink font-medium" : "text-ink-3"}>{s}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
