import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { LocationResult } from "../types/api";
import { RISK, googleMapsUrl } from "../lib/risk";
import { ExternalIcon, PinIcon } from "./icons";

const CARTO_KEY = (import.meta.env.VITE_CARTO_KEY || "").trim();
const OSM_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
const TILES = CARTO_KEY
  ? `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=${encodeURIComponent(CARTO_KEY)}`
  : "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const ATTRIBUTION = CARTO_KEY
  ? `${OSM_ATTR} &copy; <a href="https://carto.com/attributions">CARTO</a>`
  : OSM_ATTR;

function pinIcon(rank: number, color: string, selected: boolean) {
  return L.divIcon({
    className: "",
    html: `<div class="hw-pin ${selected ? "is-selected" : ""}" style="background:${color}">${rank}</div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -16],
  });
}

// Built with DOM nodes (not an HTML string) so a site name can never inject markup.
function popupContent(r: LocationResult, rank: number): HTMLElement {
  const root = document.createElement("div");
  const name = document.createElement("div");
  name.className = "hw-popup-name";
  name.textContent = `${rank}. ${r.name}`;
  const meta = document.createElement("div");
  meta.className = "hw-popup-meta";
  meta.textContent = `${RISK[r.risk_level].label} risk · score ${r.risk_score} · ${r.temperature_c.toFixed(1)} °C`;
  const coords = document.createElement("div");
  coords.className = "hw-popup-meta";
  coords.textContent = `${r.latitude.toFixed(4)}, ${r.longitude.toFixed(4)}`;
  const link = document.createElement("a");
  link.className = "hw-popup-link";
  link.href = googleMapsUrl(r.latitude, r.longitude);
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = "Open in Google Maps ↗";
  root.append(name, meta, coords, link);
  return root;
}

interface Props {
  results: LocationResult[];
  selectedIdx: number;
  onSelect: (i: number) => void;
}

export default function SiteMap({ results, selectedIdx, onSelect }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const firstSelect = useRef(true);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const [tilesFailed, setTilesFailed] = useState(false);

  // create the map once
  useEffect(() => {
    if (!el.current) return;
    const map = L.map(el.current, { scrollWheelZoom: false, zoomControl: true });
    let errors = 0;
    const tiles = L.tileLayer(TILES, { attribution: ATTRIBUTION, subdomains: "abcd", maxZoom: 19 });
    tiles.on("tileerror", () => { errors += 1; if (errors >= 3) setTilesFailed(true); });
    tiles.on("tileload", () => setTilesFailed((f) => (f ? false : f)));
    tiles.addTo(map);
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; layerRef.current = null; markersRef.current = []; };
  }, []);

  // (re)draw markers whenever results change; fit the view to all sites
  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();
    markersRef.current = results.map((r, i) => {
      const m = L.marker([r.latitude, r.longitude], {
        icon: pinIcon(i + 1, RISK[r.risk_level].solid, false),
        title: r.name,
        riseOnHover: true,
      });
      m.bindPopup(popupContent(r, i + 1));
      m.on("click", () => onSelectRef.current(i));
      m.addTo(layer);
      return m;
    });
    const pts = results.map((r) => L.latLng(r.latitude, r.longitude));
    if (pts.length === 1) map.setView(pts[0], 15);
    else map.fitBounds(L.latLngBounds(pts), { padding: [60, 60], maxZoom: 15 });
    firstSelect.current = true;
  }, [results]);

  // highlight the selected site; open its popup after the first interaction
  useEffect(() => {
    const map = mapRef.current;
    markersRef.current.forEach((m, i) => {
      const r = results[i];
      if (r) m.setIcon(pinIcon(i + 1, RISK[r.risk_level].solid, i === selectedIdx));
    });
    const m = markersRef.current[selectedIdx];
    if (!map || !m) return;
    if (firstSelect.current) { firstSelect.current = false; return; }
    map.panTo(m.getLatLng());
    m.openPopup();
  }, [selectedIdx, results]);

  return (
    <div className="rounded-lg border border-line bg-white overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-b border-line">
        <div>
          <h3 className="text-sm font-semibold text-ink">Where the sites are</h3>
          <p className="text-xs text-ink-3 mt-0.5">Pins are numbered by rank and coloured by risk. Click a pin, then open it in Google Maps.</p>
        </div>
        <ul className="flex items-center gap-4 text-xs text-ink-2">
          {(["LOW", "MODERATE", "HIGH", "CRITICAL"] as const).map((l) => (
            <li key={l} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: RISK[l].solid }} />
              {RISK[l].label}
            </li>
          ))}
        </ul>
      </div>

      <div className="hw-map relative isolate">
        <div ref={el} className="h-[380px] w-full" role="region" aria-label="Map of the analysed sites" />
        {tilesFailed && (
          <div className="absolute left-3 bottom-8 right-3 sm:right-auto sm:max-w-sm rounded-md bg-white/95 border border-line px-3 py-2 text-xs text-ink-2 shadow-card z-[500]">
            Map tiles need an internet connection. Pins are still placed correctly; use the links below to open each site.
          </div>
        )}
      </div>

      <ul className="grid sm:grid-cols-2 lg:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-line border-t border-line">
        {results.map((r, i) => (
          <li key={r.name} className="px-6 py-4">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full text-[11px] font-bold text-white flex items-center justify-center" style={{ background: RISK[r.risk_level].solid }}>
                {i + 1}
              </span>
              <span className="font-medium text-[15px] truncate">{r.name}</span>
            </div>
            <p className="mt-1 text-xs text-ink-3 tnum flex items-center gap-1">
              <PinIcon className="w-3 h-3" /> {r.latitude.toFixed(4)}, {r.longitude.toFixed(4)}
            </p>
            <a
              href={googleMapsUrl(r.latitude, r.longitude)}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-brand hover:text-brand-dark"
            >
              Open in Google Maps <ExternalIcon />
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
