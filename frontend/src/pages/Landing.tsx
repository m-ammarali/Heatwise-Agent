import { Link } from "react-router-dom";
import { ArrowRight, CheckIcon, CloseIcon } from "../components/icons";
import { RISK } from "../lib/risk";
import type { RiskLevel } from "../types/api";

/* Figures below are from real HeatWise runs on Lahore sites (replay of 10 June 2026 and 16 October 2026). */
const REPLAY: { name: string; score: number; level: RiskLevel; adj: string }[] = [
  { name: "Bagh-e-Jinnah", score: 66, level: "HIGH", adj: "−3.5 °C" },
  { name: "Gaddafi Stadium", score: 87, level: "CRITICAL", adj: "+0.3 °C" },
  { name: "Anarkali Bazaar", score: 89, level: "CRITICAL", adj: "+0.5 °C" },
];

function PreviewFrame() {
  const windows: [string, number, string][] = [
    ["Best", 3, "#1f9d63"],
    ["Caution", 2, "#e0a100"],
    ["Avoid", 7, "#d23a52"],
    ["Recovery", 4, "#1d4ba0"],
  ];
  return (
    <div className="rounded-xl border border-line bg-white shadow-card overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-line bg-soft">
        <span className="w-2.5 h-2.5 rounded-full bg-[#d6dbe4]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#d6dbe4]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#d6dbe4]" />
        <span className="ml-3 rounded bg-white border border-line px-3 py-0.5 text-xs text-ink-3">
          Sample result · Lahore · 10 June 2026 replay
        </span>
      </div>
      <div className="p-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">Ranking at 14:00</p>
        <ul className="mt-3 space-y-3">
          {REPLAY.map((r, i) => (
            <li key={r.name} className="flex items-center gap-3">
              <span className="w-5 h-5 rounded-full text-[11px] font-bold text-white flex items-center justify-center" style={{ background: RISK[r.level].solid }}>{i + 1}</span>
              <span className="w-32 text-sm font-medium truncate">{r.name}</span>
              <div className="flex-1 h-2 rounded-full bg-line overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${r.score}%`, background: RISK[r.level].solid }} />
              </div>
              <span className="w-7 text-right text-sm font-semibold tnum">{r.score}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-ink-3">Same 43.0 °C regional forecast at all three. The park scores lower because of what surrounds it.</p>

        <p className="mt-6 text-xs font-semibold uppercase tracking-wider text-ink-3">Work windows · Bagh-e-Jinnah</p>
        <div className="mt-3 flex h-6 rounded overflow-hidden">
          {windows.map(([label, hrs, color]) => (
            <div key={label} style={{ flex: hrs, background: color }} className="border-r-2 border-white last:border-0" title={label} />
          ))}
        </div>
        <div className="mt-1.5 flex justify-between text-[11px] text-ink-3 tnum"><span>05:00</span><span>10:00</span><span>17:00</span><span>21:00</span></div>
      </div>
    </div>
  );
}

const STATS: [string, string][] = [
  ["1–5", "sites compared per analysis"],
  ["250 m", "of surroundings read around each pin"],
  ["5", "weighted factors in every score"],
  ["0", "API keys needed to run it"],
];

const STEPS: [string, string, string][] = [
  ["01", "Observe", "Pull the hourly weather for each site and date."],
  ["02", "Analyze", "Read pavement, buildings, trees and water around each pin."],
  ["03", "Investigate", "Decide whether the site is risky enough to deserve a deep report."],
  ["04", "Decide", "Rank the sites and write down the evidence behind the ranking."],
  ["05", "Act", "Produce work windows and a prioritised action plan."],
];

const WEIGHTS: [string, number][] = [
  ["Temperature", 45],
  ["Heat index", 20],
  ["Solar exposure", 20],
  ["Paved surface", 10],
  ["Lack of vegetation", 5],
];

const COMPARE: { row: string; weather: string; calc: string; hw: string }[] = [
  { row: "Temperature for the exact site", weather: "One number for the city", calc: "You type it in", hw: "Per site, adjusted for surroundings" },
  { row: "Shade and pavement nearby", weather: "—", calc: "—", hw: "Read within 250 m" },
  { row: "Ranks several sites", weather: "—", calc: "—", hw: "Up to five at once" },
  { row: "Safe hours of the day", weather: "Hourly temperatures", calc: "—", hw: "Best / Caution / Avoid / Recovery" },
  { row: "Explains the result", weather: "—", calc: "A formula", hw: "Every weight and signal shown" },
  { row: "Cost to run", weather: "Free", calc: "Free", hw: "Free, on open data" },
];

export default function Landing() {
  return (
    <div>
      {/* HERO */}
      <section className="hero-glow">
        <div className="max-w-6xl mx-auto px-6 pt-16 pb-20 md:pt-24 grid lg:grid-cols-[1.2fr_1fr] gap-12 items-center">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-line-strong bg-white px-3.5 py-1.5 text-xs font-semibold tracking-[0.14em] text-ink-2 uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-accent" /> Outdoor heat-risk decisions
            </span>
            <h1 className="mt-6 text-[2.5rem] md:text-5xl lg:text-[3.1rem] font-bold tracking-tight leading-[1.08]">
              Pick the safer site
              <br />
              <span className="text-brand">before the shift starts.</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-2">
              HeatWise compares up to five job sites by what surrounds them — pavement, shade, sun — and tells your crew
              where to work and which hours to avoid. It runs on open weather and map data.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-md bg-brand hover:bg-brand-dark text-white font-semibold px-6 py-3.5 transition-colors">
                Analyze your sites <ArrowRight />
              </Link>
              <a href="#how" className="inline-flex items-center rounded-md border border-line-strong bg-white hover:bg-soft font-semibold px-6 py-3.5 transition-colors">
                See how it works
              </a>
            </div>
            <ul className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-2">
              {["No account or API key", "PDF brief for risky sites", "Works from cached data offline"].map((t) => (
                <li key={t} className="flex items-center gap-2"><span className="text-brand"><CheckIcon /></span>{t}</li>
              ))}
            </ul>
          </div>
          <PreviewFrame />
        </div>

        <div className="max-w-6xl mx-auto px-6 pb-16">
          <dl className="grid grid-cols-2 md:grid-cols-4 rounded-lg border border-line bg-white divide-x divide-line">
            {STATS.map(([n, label]) => (
              <div key={label} className="px-6 py-5">
                <dt className="text-2xl md:text-3xl font-bold tracking-tight tnum">{n}</dt>
                <dd className="mt-1 text-[11px] font-semibold uppercase tracking-wider text-ink-3">{label}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* WHAT IT IS */}
      <section className="border-t border-line">
        <div className="max-w-6xl mx-auto px-6 py-20 grid lg:grid-cols-2 gap-14 items-start">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-3">What is HeatWise</p>
            <h2 className="mt-4 text-3xl md:text-4xl font-bold tracking-tight leading-tight">
              A heat tool that respects your supervisor's time
            </h2>
            <p className="mt-5 text-ink-2 leading-relaxed">
              A city forecast says it is hot. It cannot say which of your three sites is worse, or which hours to
              keep the crew off the roof. HeatWise answers those two questions and writes down why, so the decision
              can be checked by anyone.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 gap-px bg-line border border-line rounded-lg overflow-hidden">
            {[
              ["Built for site supervisors", "Construction, delivery, utilities, city operations and event crews."],
              ["Ranks sites, not cities", "Compare the real alternatives you are choosing between."],
              ["Every number is auditable", "Weights, signals and each step the agent took are visible."],
              ["Runs on open data", "Open-Meteo and OpenStreetMap. Nothing to buy or sign up for."],
            ].map(([t, d]) => (
              <div key={t} className="bg-white p-6">
                <span className="text-brand"><CheckIcon /></span>
                <h3 className="mt-3 text-[15px] font-semibold">{t}</h3>
                <p className="mt-1.5 text-sm text-ink-2 leading-relaxed">{d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="bg-soft border-y border-line">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-3">How it works</p>
          <h2 className="mt-4 text-3xl md:text-4xl font-bold tracking-tight">One pipeline, five stages</h2>
          <ol className="mt-10 grid md:grid-cols-5 gap-px bg-line border border-line rounded-lg overflow-hidden">
            {STEPS.map(([n, t, d]) => (
              <li key={n} className="bg-white p-6">
                <span className="text-xs font-bold text-accent tnum">{n}</span>
                <h3 className="mt-2 text-base font-semibold">{t}</h3>
                <p className="mt-2 text-sm text-ink-2 leading-relaxed">{d}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* WHY */}
      <section id="why" className="max-w-6xl mx-auto px-6 py-24 space-y-24">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-3">Why HeatWise</p>
          <h2 className="mt-4 text-3xl md:text-4xl font-bold tracking-tight">Three things it does differently</h2>
        </div>

        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="rounded-lg border border-line bg-white p-6 shadow-card order-2 md:order-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">Land-cover adjustment · same 43.0 °C forecast</p>
            <ul className="mt-5 space-y-4">
              {REPLAY.map((r) => {
                const v = parseFloat(r.adj.replace("−", "-").replace(" °C", ""));
                const w = (Math.abs(v) / 3.5) * 50;
                return (
                  <li key={r.name} className="flex items-center gap-3 text-sm">
                    <span className="w-32 truncate">{r.name}</span>
                    <div className="relative flex-1 h-4">
                      <span className="absolute left-1/2 inset-y-0 w-px bg-line-strong" />
                      <span
                        className="absolute inset-y-0.5 rounded-sm"
                        style={{ background: v < 0 ? "#1f9d63" : "#d23a52", width: `${w}%`, left: v < 0 ? `${50 - w}%` : "50%" }}
                      />
                    </div>
                    <span className="w-16 text-right font-semibold tnum">{r.adj}</span>
                  </li>
                );
              })}
            </ul>
          </div>
          <div className="order-1 md:order-2">
            <span className="text-xs font-bold text-accent">01</span>
            <h3 className="mt-2 text-2xl font-semibold tracking-tight">It reads the surroundings, not just the city</h3>
            <p className="mt-3 text-ink-2 leading-relaxed">
              Weather models are coarse, so nearby sites get the same temperature. HeatWise adds a bounded adjustment
              from the pavement, buildings, trees and water within 250 m of each pin. It is a modelled estimate and is
              labelled as one on every result.
            </p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <span className="text-xs font-bold text-accent">02</span>
            <h3 className="mt-2 text-2xl font-semibold tracking-tight">A score you can audit</h3>
            <p className="mt-3 text-ink-2 leading-relaxed">
              The 0–100 operational risk score is a plain weighted sum. No hidden model: you can see each factor,
              its weight, and how much it contributed to the final number.
            </p>
          </div>
          <div className="rounded-lg border border-line bg-white p-6 shadow-card">
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">Score weights</p>
            <ul className="mt-5 space-y-3.5">
              {WEIGHTS.map(([k, w]) => (
                <li key={k} className="flex items-center gap-3 text-sm">
                  <span className="w-36">{k}</span>
                  <div className="flex-1 h-2 rounded-full bg-line"><div className="h-full rounded-full bg-brand" style={{ width: `${w * 2}%` }} /></div>
                  <span className="w-10 text-right font-semibold tnum">{w}%</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="rounded-lg border border-line bg-white p-6 shadow-card order-2 md:order-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">Two real runs, same three sites</p>
            <div className="mt-5 space-y-4 text-sm">
              <div className="rounded-md bg-soft border border-line p-4">
                <p className="font-semibold">16 October · scores 9, 23, 25</p>
                <p className="mt-1 text-ink-2">Low and moderate. Deep report skipped, nothing spent.</p>
              </div>
              <div className="rounded-md bg-[#fce8eb] border border-[#f1b9c3] p-4">
                <p className="font-semibold text-[#a3263c]">10 June replay · scores 66, 87, 89</p>
                <p className="mt-1 text-ink-2">High and critical. A PDF brief was generated for each site.</p>
              </div>
            </div>
          </div>
          <div className="order-1 md:order-2">
            <span className="text-xs font-bold text-accent">03</span>
            <h3 className="mt-2 text-2xl font-semibold tracking-tight">It digs deeper only when it matters</h3>
            <p className="mt-3 text-ink-2 leading-relaxed">
              The expensive step — a written Heat Intelligence brief — runs only for sites the agent itself scores
              HIGH or CRITICAL. Every skip and every investigation is recorded in the decision trace.
            </p>
          </div>
        </div>
      </section>

      {/* COMPARE */}
      <section id="compare" className="bg-soft border-y border-line">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-3">Comparison</p>
          <h2 className="mt-4 text-3xl md:text-4xl font-bold tracking-tight">How HeatWise compares</h2>
          <div className="mt-8 rounded-lg border border-line bg-white overflow-x-auto">
            <table className="w-full min-w-[760px] text-sm">
              <thead>
                <tr className="bg-navy text-left text-xs font-semibold text-white">
                  <th className="px-5 py-3.5 w-[26%]">Question</th>
                  <th className="px-5 py-3.5">City weather forecast</th>
                  <th className="px-5 py-3.5">Heat-index calculator</th>
                  <th className="px-5 py-3.5"><span className="inline-flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-accent" />HeatWise</span></th>
                </tr>
              </thead>
              <tbody>
                {COMPARE.map((r) => (
                  <tr key={r.row} className="border-t border-line">
                    <td className="px-5 py-4 font-medium">{r.row}</td>
                    <td className="px-5 py-4 text-ink-2">{r.weather}</td>
                    <td className="px-5 py-4 text-ink-2">{r.calc}</td>
                    <td className="px-5 py-4 font-medium text-brand">{r.hw}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FIT */}
      <section id="fit" className="max-w-6xl mx-auto px-6 py-24">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-3">Fit check</p>
        <h2 className="mt-4 text-3xl md:text-4xl font-bold tracking-tight">Is HeatWise right for your work?</h2>
        <p className="mt-3 text-ink-2">It is a focused decision aid, not everything for everyone. Here is how to tell.</p>
        <div className="mt-8 grid md:grid-cols-2 gap-6">
          <div className="rounded-lg border border-line p-7 bg-white shadow-card">
            <h3 className="font-semibold flex items-center gap-2"><span className="w-6 h-6 rounded bg-brand text-white flex items-center justify-center"><CheckIcon className="w-3.5 h-3.5" /></span>A good fit if…</h3>
            <ul className="mt-5 space-y-3 text-sm text-ink-2">
              {[
                "You choose between several outdoor sites or shift times.",
                "You want a recommendation you can explain to a crew or a manager.",
                "You want something that works with no account, key or budget.",
                "You can accept a modelled estimate for site temperature.",
              ].map((t) => <li key={t} className="flex gap-3"><span className="text-brand mt-0.5"><CheckIcon className="w-4 h-4" /></span>{t}</li>)}
            </ul>
          </div>
          <div className="rounded-lg border border-line p-7 bg-soft">
            <h3 className="font-semibold flex items-center gap-2"><span className="w-6 h-6 rounded bg-ink-3 text-white flex items-center justify-center"><CloseIcon className="w-3.5 h-3.5" /></span>Probably not, if…</h3>
            <ul className="mt-5 space-y-3 text-sm text-ink-2">
              {[
                "You need measured, sensor-grade temperatures at the work face.",
                "You need a medical or regulatory heat-illness assessment.",
                "Your area is barely mapped in OpenStreetMap (a confidence level is shown).",
                "You need guaranteed live data with no internet fallback.",
              ].map((t) => <li key={t} className="flex gap-3"><span className="text-ink-3 mt-0.5"><CloseIcon className="w-4 h-4" /></span>{t}</li>)}
            </ul>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-navy text-white">
        <div className="max-w-4xl mx-auto px-6 py-20 text-center">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight">Stop guessing which site is hotter.</h2>
          <p className="mt-4 text-[#c3cde6] max-w-xl mx-auto">Enter your sites, pick a date, and get a ranked answer with the reasons attached.</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-md bg-white text-navy font-semibold px-6 py-3.5 hover:bg-[#eaf0fb] transition-colors">
              Analyze your sites <ArrowRight />
            </Link>
            <Link to="/dashboard?demo=1" className="inline-flex items-center rounded-md border border-[#3b4d7d] text-white font-semibold px-6 py-3.5 hover:bg-[#182a5c] transition-colors">
              Try the Lahore example
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
