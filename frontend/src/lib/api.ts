import type {
  AnalyzeRequestBody,
  AnalyzeResponse,
  HistoryEntry,
  StatusResponse,
} from "../types/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = "Something went wrong talking to the HeatWise backend.";
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore parse errors, use default message */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getStatus: () => request<StatusResponse>("/status"),
  analyze: (body: AnalyzeRequestBody) =>
    request<AnalyzeResponse>("/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getHistory: () => request<HistoryEntry[]>("/history"),
  getHistoryDetail: (requestId: string) =>
    request<AnalyzeResponse>(`/history/${requestId}`),
};
