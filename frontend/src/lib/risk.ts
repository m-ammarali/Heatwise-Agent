import type { LocationResult, RiskLevel } from "../types/api";

export const RISK: Record<RiskLevel, { label: string; solid: string; text: string; bg: string; border: string }> = {
  LOW: { label: "Low", solid: "#1f9d63", text: "#14724a", bg: "#e8f6ef", border: "#bfe3d0" },
  MODERATE: { label: "Moderate", solid: "#e0a100", text: "#7d5700", bg: "#fff5d9", border: "#f2dc9b" },
  HIGH: { label: "High", solid: "#e8750f", text: "#a04a08", bg: "#feeedb", border: "#f6cfa6" },
  CRITICAL: { label: "Critical", solid: "#d23a52", text: "#a3263c", bg: "#fce8eb", border: "#f1b9c3" },
};

export function levelFromScore(score: number): RiskLevel {
  if (score >= 75) return "CRITICAL";
  if (score >= 50) return "HIGH";
  if (score >= 25) return "MODERATE";
  return "LOW";
}

export function googleMapsUrl(lat: number, lon: number): string {
  return `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
}

export function sourceLabel(ds: LocationResult["data_source"]): string {
  if (ds === "demo") return "Demo data (not live)";
  if (ds === "open_data") return "Live open data";
  return "Live data";
}

export function localToday(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
