import { useEffect, useState } from "react";
import { Routes, Route, NavLink, Link } from "react-router-dom";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Logo from "./components/Logo";
import { ArrowRight } from "./components/icons";
import { api } from "./lib/api";

function NavBar() {
  const [live, setLive] = useState<boolean | null>(null);
  const [label, setLabel] = useState("");
  const [qwen, setQwen] = useState(false);

  useEffect(() => {
    api
      .getStatus()
      .then((s) => { setLive(s.live_data_available); setLabel(s.provider_label); setQwen(s.qwen_enabled); })
      .catch(() => setLive(false));
  }, []);

  const link = ({ isActive }: { isActive: boolean }) =>
    `text-[15px] font-medium transition-colors ${isActive ? "text-ink" : "text-ink-2 hover:text-ink"}`;

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-line">
      <div className="max-w-6xl mx-auto px-6 h-[68px] flex items-center justify-between gap-6">
        <Link to="/" className="flex items-center gap-2.5">
          <Logo />
          <span className="text-xl font-bold tracking-tight">HeatWise</span>
        </Link>
        <nav className="hidden md:flex items-center gap-8">
          <a href="/#how" className="text-[15px] font-medium text-ink-2 hover:text-ink">How it works</a>
          <a href="/#compare" className="text-[15px] font-medium text-ink-2 hover:text-ink">Compare</a>
          <NavLink to="/dashboard" className={link}>Analyze</NavLink>
          <NavLink to="/history" className={link}>History</NavLink>
        </nav>
        <div className="flex items-center gap-4">
          <span
            className="hidden lg:flex items-center gap-2 text-xs text-ink-2"
            title={live ? "Live data source reachable" : "No live data source: demo data will be used"}
          >
            <span className={`w-2 h-2 rounded-full ${live === null ? "bg-ink-3" : live ? "bg-[#1f9d63]" : "bg-[#e0a100]"}`} />
            {live === null ? "Checking…" : live ? `Live: ${label.replace(/ \(.*\)/, "")}${qwen ? " + Qwen" : ""}` : "Demo mode"}
          </span>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-1.5 rounded-md bg-brand hover:bg-brand-dark text-white text-sm font-semibold px-4 py-2.5 transition-colors"
          >
            Analyze sites <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-line bg-white">
      <div className="max-w-6xl mx-auto px-6 py-12 grid md:grid-cols-[1.4fr_1fr_1fr] gap-10 text-sm">
        <div>
          <div className="flex items-center gap-2.5"><Logo size={28} /><span className="text-lg font-bold tracking-tight">HeatWise</span></div>
          <p className="mt-4 max-w-sm text-ink-2 leading-relaxed">
            An operational decision aid for outdoor work in the heat. It is not a substitute for official weather alerts,
            occupational-safety rules or medical advice.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">Data</p>
          <ul className="mt-3 space-y-2 text-ink-2">
            <li>Weather by <a className="underline hover:text-ink" href="https://open-meteo.com/" target="_blank" rel="noreferrer">Open-Meteo.com</a> (CC BY 4.0)</li>
            <li>Map data © <a className="underline hover:text-ink" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors (ODbL)</li>
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-ink-3">Project</p>
          <ul className="mt-3 space-y-2 text-ink-2">
            <li>Alibaba Cloud AI Hackathon Pakistan 2026</li>
            <li>Built by M. Ammar, M. Mubashar, M. Hanzala and M. Hamza</li>
          </ul>
        </div>
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <NavBar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
