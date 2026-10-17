export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

export interface LocationIn {
  name: string;
  latitude: number;
  longitude: number;
}

export interface AnalyzeRequestBody {
  locations: LocationIn[];
  analysis_date: string;
  analysis_hour: string;
  deep_investigation: boolean;
  demo_mode: boolean;
}

export interface EvidenceSignal {
  label: string;
  direction: "up" | "down" | "neutral";
  detail: string;
}

export interface WorkWindow {
  label: "BEST" | "CAUTION" | "AVOID" | "RECOVERY";
  start: string;
  end: string;
  note: string;
}

export interface ActionPlanItem {
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  action: string;
  reason: string;
  supporting_data: string[];
}

export interface HeatIntelligenceInfo {
  requested: boolean;
  categories: string[];
  reason: string;
  pdf_available: boolean;
  pdf_relative_path?: string | null;
}

export interface LocationResult {
  name: string;
  latitude: number;
  longitude: number;
  temperature_c: number;
  temperature_f: number;
  risk_score: number;
  risk_level: RiskLevel;
  primary_driver: string;
  recommended_action: string;
  evidence: EvidenceSignal[];
  work_windows: WorkWindow[];
  action_plan: ActionPlanItem[];
  heat_intelligence: HeatIntelligenceInfo;
  solar_ghi?: number | null;
  solar_dni?: number | null;
  solar_dhi?: number | null;
  tree_canopy_pct?: number | null;
  impervious_pct?: number | null;
  data_source: "live" | "open_data" | "demo";
}

export interface DecisionTraceStep {
  step: number;
  description: string;
}

export interface AnalyzeResponse {
  request_id: string;
  generated_at: string;
  demo_mode: boolean;
  preferred_site: string;
  decision_summary: string;
  results: LocationResult[];
  decision_trace: DecisionTraceStep[];
  data_provider?: string;
  ai_briefing?: string | null;
}

export interface HistoryEntry {
  request_id: string;
  generated_at: string;
  demo_mode: boolean;
  preferred_site: string;
  location_names: string[];
  max_risk_score: number;
}

export interface StatusResponse {
  provider: string;
  provider_label: string;
  live_data_available: boolean;
  qwen_enabled: boolean;
  detail: string;
}
