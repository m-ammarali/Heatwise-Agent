import type { WorkWindow } from "../types/api";

const STYLE: Record<WorkWindow["label"], { bar: string; text: string; bg: string; title: string }> = {
  BEST: { bar: "#1f9d63", text: "#14724a", bg: "#e8f6ef", title: "Best" },
  CAUTION: { bar: "#e0a100", text: "#7d5700", bg: "#fff5d9", title: "Caution" },
  AVOID: { bar: "#d23a52", text: "#a3263c", bg: "#fce8eb", title: "Avoid" },
  RECOVERY: { bar: "#1d4ba0", text: "#153a80", bg: "#eaf0fb", title: "Recovery" },
};

const toH = (t: string) => {
  const [h, m] = t.split(":").map(Number);
  return h + (m || 0) / 60;
};

export default function WorkWindowTimeline({ windows }: { windows: WorkWindow[] }) {
  const start = Math.min(...windows.map((w) => toH(w.start)));
  const end = Math.max(...windows.map((w) => toH(w.end)));
  const span = Math.max(1, end - start);
  const ticks: number[] = [];
  for (let h = Math.ceil(start); h <= end; h += 2) ticks.push(h);

  return (
    <div className="rounded-lg border border-line bg-white p-6 h-full">
      <h3 className="text-sm font-semibold text-ink">Work windows for the day</h3>

      <div className="mt-5">
        <div className="relative h-7 rounded bg-line overflow-hidden">
          {windows.map((w, i) => (
            <div
              key={i}
              title={`${STYLE[w.label].title} ${w.start}–${w.end}`}
              style={{
                left: `${((toH(w.start) - start) / span) * 100}%`,
                width: `${((toH(w.end) - toH(w.start)) / span) * 100}%`,
                background: STYLE[w.label].bar,
              }}
              className="absolute inset-y-0 border-r-2 border-white"
            />
          ))}
        </div>
        <div className="relative h-5 mt-1.5 text-[11px] text-ink-3 tnum">
          {ticks.map((h) => {
            const pct = ((h - start) / span) * 100;
            const shift = pct < 4 ? "" : pct > 96 ? "-translate-x-full" : "-translate-x-1/2";
            return (
              <span key={h} className={`absolute ${shift}`} style={{ left: `${pct}%` }}>
                {String(h).padStart(2, "0")}:00
              </span>
            );
          })}
        </div>
      </div>

      <ul className="mt-4 space-y-3">
        {windows.map((w, i) => (
          <li key={i} className="flex gap-3 items-start">
            <span
              className="shrink-0 mt-0.5 w-[78px] text-center rounded px-2 py-0.5 text-xs font-semibold"
              style={{ background: STYLE[w.label].bg, color: STYLE[w.label].text }}
            >
              {STYLE[w.label].title}
            </span>
            <div>
              <p className="text-[15px] font-medium tnum">{w.start} – {w.end}</p>
              <p className="text-sm text-ink-2 leading-snug">{w.note}</p>
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-5 text-xs text-ink-3">Operational guidance only, not a medical or occupational-safety directive.</p>
    </div>
  );
}
