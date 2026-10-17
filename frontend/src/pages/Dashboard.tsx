import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import LocationInputList from "../components/LocationInputList";
import AgentActivityPanel from "../components/AgentActivityPanel";
import { DecisionHero, RiskScoreCard, ComparisonTable } from "../components/ResultsOverview";
import EvidencePanel from "../components/EvidencePanel";
import WorkWindowTimeline from "../components/WorkWindowTimeline";
import ActionPlanList from "../components/ActionPlanList";
import SiteMap from "../components/SiteMap";
import { DecisionTracePanel, HeatIntelligenceBadge } from "../components/DecisionTracePanel";
import { ArrowLeft, ArrowRight } from "../components/icons";
import { LAHORE_DEMO_SCENARIO } from "../lib/demoScenario";
import { localToday } from "../lib/risk";
import { api } from "../lib/api";
import type { AnalyzeResponse, LocationIn } from "../types/api";

type Stage = "input" | "loading" | "results" | "error";

const checkbox = "mt-0.5 w-4 h-4 rounded border-line-strong accent-[#1d4ba0]";

export default function Dashboard() {
  const [params] = useSearchParams();
  const isDemoQuery = params.get("demo") === "1";

  const [locations, setLocations] = useState<LocationIn[]>(
    isDemoQuery ? LAHORE_DEMO_SCENARIO : [{ name: "", latitude: 0, longitude: 0 }]
  );
  const [demoMode, setDemoMode] = useState(false);
  const [deepInvestigation, setDeepInvestigation] = useState(false);
  const [analysisDate, setAnalysisDate] = useState(localToday());
  const [stage, setStage] = useState<Stage>("input");
  const [response, setResponse] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedIdx, setSelectedIdx] = useState(0);

  const validLocations = locations.filter((l) => l.name.trim() && (l.latitude !== 0 || l.longitude !== 0));

  async function runAnalysis() {
    setStage("loading");
    setError(null);
    try {
      const resp = await api.analyze({
        locations: validLocations,
        analysis_date: analysisDate,
        analysis_hour: "14:00",
        deep_investigation: deepInvestigation,
        demo_mode: demoMode,
      });
      setTimeout(() => {
        setResponse(resp);
        setSelectedIdx(0);
        setStage("results");
        window.scrollTo({ top: 0 });
      }, 500);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed.");
      setStage("error");
    }
  }

  function reset() {
    setStage("input");
    setResponse(null);
    window.scrollTo({ top: 0 });
  }

  const selected = response?.results[selectedIdx];
  const top = response?.results[0];

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 md:py-14">
      {stage !== "results" && (
        <header className="mb-8">
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">Analyze your sites</h1>
          <p className="mt-2 text-ink-2 text-base max-w-2xl">
            Add up to five candidate sites and a date. HeatWise ranks them and shows the hours to avoid.
          </p>
        </header>
      )}

      {stage === "input" && (
        <div className="grid lg:grid-cols-[1fr_320px] gap-8 items-start">
          <div className="rounded-lg border border-line bg-white p-6 md:p-8 shadow-card">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-sm font-semibold">Sites</h2>
              <button
                onClick={() => setLocations(LAHORE_DEMO_SCENARIO)}
                className="text-sm font-medium text-brand hover:text-brand-dark"
              >
                Fill with Lahore example
              </button>
            </div>
            <LocationInputList locations={locations} onChange={setLocations} />

            <div className="mt-8 pt-6 border-t border-line grid sm:grid-cols-2 gap-6">
              <label className="block">
                <span className="text-sm font-medium">Analysis date</span>
                <input
                  type="date"
                  value={analysisDate}
                  onChange={(e) => setAnalysisDate(e.target.value)}
                  className="mt-1.5 block w-full rounded-md border border-line-strong bg-white px-3 py-2.5 text-[15px] tnum focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
                />
                <span className="mt-1.5 block text-xs text-ink-3">Past dates and up to about 16 days ahead. Time of day: 14:00.</span>
              </label>

              <div className="space-y-4">
                <label className="flex gap-3 cursor-pointer">
                  <input type="checkbox" checked={deepInvestigation} onChange={(e) => setDeepInvestigation(e.target.checked)} className={checkbox} />
                  <span>
                    <span className="block text-sm font-medium">Always run the deep investigation</span>
                    <span className="block text-xs text-ink-3 mt-0.5">Otherwise it runs only for HIGH and CRITICAL sites.</span>
                  </span>
                </label>
                <label className="flex gap-3 cursor-pointer">
                  <input type="checkbox" checked={demoMode} onChange={(e) => setDemoMode(e.target.checked)} className={checkbox} />
                  <span>
                    <span className="block text-sm font-medium">Use demo data (offline)</span>
                    <span className="block text-xs text-ink-3 mt-0.5">Bundled sample values. Results are labelled as demo.</span>
                  </span>
                </label>
              </div>
            </div>

            <button
              disabled={validLocations.length === 0}
              onClick={runAnalysis}
              className="mt-8 inline-flex items-center gap-2 rounded-md bg-brand hover:bg-brand-dark disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-[15px] px-6 py-3 transition-colors"
            >
              Analyze {validLocations.length > 1 ? `${validLocations.length} sites` : "site"} <ArrowRight />
            </button>
          </div>

          <aside className="rounded-lg bg-soft border border-line p-6 text-sm text-ink-2 leading-relaxed">
            <h2 className="text-sm font-semibold text-ink">Before you run</h2>
            <ul className="mt-3 space-y-3">
              <li><span className="font-medium text-ink">Get coordinates:</span> right-click a spot in Google Maps and click the numbers to copy them.</li>
              <li><span className="font-medium text-ink">Place the pin on the work area itself.</span> HeatWise reads the surroundings within 250 m.</li>
              <li><span className="font-medium text-ink">Compare real alternatives.</span> Sites in the same city work well: they share a forecast and differ in surroundings.</li>
              <li><span className="font-medium text-ink">First run is slower.</span> Map data is fetched once, then cached.</li>
            </ul>
          </aside>
        </div>
      )}

      {stage === "loading" && <div className="py-6"><AgentActivityPanel /></div>}

      {stage === "error" && (
        <div className="max-w-lg rounded-lg border border-[#f1b9c3] bg-[#fce8eb] p-6">
          <p className="text-sm font-semibold text-[#a3263c]">The analysis could not be completed.</p>
          <p className="mt-1 text-sm text-ink-2">{error}</p>
          <button onClick={reset} className="mt-4 text-sm font-medium text-brand hover:text-brand-dark">Try again</button>
        </div>
      )}

      {stage === "results" && response && selected && top && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <button onClick={reset} className="inline-flex items-center gap-1.5 text-sm font-medium text-brand hover:text-brand-dark">
                <ArrowLeft /> New analysis
              </button>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight">Results</h1>
              <p className="mt-1 text-sm text-ink-2 tnum">
                {analysisDate} at 14:00 · {response.results.length} site{response.results.length > 1 ? "s" : ""} ·{" "}
                {response.data_provider || "Open data"}
              </p>
            </div>
          </div>

          {response.demo_mode && (
            <div className="rounded-md border border-[#f2dc9b] bg-[#fff5d9] px-4 py-3 text-sm text-[#7d5700]">
              <span className="font-semibold">Demo data.</span> These values are bundled samples, not live results.
            </div>
          )}

          <DecisionHero result={top} siteCount={response.results.length} summary={response.decision_summary} />

          {response.ai_briefing && (
            <div className="rounded-lg border border-line bg-white p-6">
              <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">Supervisor briefing · written by Qwen on Alibaba Cloud</p>
              <p className="mt-2 text-[15px] leading-relaxed">{response.ai_briefing}</p>
            </div>
          )}

          <ComparisonTable results={response.results} selectedIdx={selectedIdx} onSelect={setSelectedIdx} />

          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-3 mb-3">Detail for</p>
            <div role="tablist" className="flex flex-wrap gap-2">
              {response.results.map((r, i) => (
                <button
                  key={r.name}
                  role="tab"
                  aria-selected={selectedIdx === i}
                  onClick={() => setSelectedIdx(i)}
                  className={`px-4 py-2 rounded-md text-sm font-medium border transition-colors ${
                    selectedIdx === i ? "bg-ink text-white border-ink" : "bg-white text-ink-2 border-line-strong hover:border-ink-3 hover:text-ink"
                  }`}
                >
                  {i + 1}. {r.name}
                </button>
              ))}
            </div>
          </div>

          {/* the four boxes */}
          <div className="grid md:grid-cols-2 gap-6 items-start">
            <div className="space-y-6">
              <RiskScoreCard result={selected} />
              <WorkWindowTimeline windows={selected.work_windows} />
            </div>
            <div className="space-y-6">
              <EvidencePanel evidence={selected.evidence} />
              <ActionPlanList items={selected.action_plan} />
            </div>
          </div>

          {/* map, full width under the four boxes */}
          <SiteMap results={response.results} selectedIdx={selectedIdx} onSelect={setSelectedIdx} />

          <HeatIntelligenceBadge info={selected.heat_intelligence} />
          <DecisionTracePanel trace={response.decision_trace} />
        </div>
      )}
    </div>
  );
}
