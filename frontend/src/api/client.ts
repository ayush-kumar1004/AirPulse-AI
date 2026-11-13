// THE single shared API client. Owner: Person D. Change only by team agreement.
// Paths mirror the DOCX Section 6 contract EXACTLY. Never fetch a backend URL directly elsewhere.

// Resolve backend API URL with cloud production fallback
const rawBase = (import.meta.env.VITE_API_BASE_URL || "").trim();
let calculatedBase = rawBase;
if (!calculatedBase) {
  calculatedBase = typeof window !== "undefined" && window.location.hostname.includes("onrender.com")
    ? "https://airpulse-backend-jv0l.onrender.com"
    : "http://localhost:8000";
} else if (!calculatedBase.startsWith("http://") && !calculatedBase.startsWith("https://")) {
  calculatedBase = `https://${calculatedBase}`;
}
const BASE = calculatedBase.replace(/\/+$/, "");

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

// --- Person A: data ---
// NOTE: every endpoint uses `ward_id` as the query param (not `ward` as in the original contract
// draft) — Person A's real implementation set this, and B/C's endpoints now match for consistency.
export const getWards = () => get<any>("/api/wards");
export const getAQI = (wardId: string) => get<any>(`/api/aqi?ward_id=${wardId}`);
export const getAQIHistory = (wardId: string, days = 1) => get<any[]>(`/api/aqi/history?ward_id=${wardId}&days=${days}`);
export const getWeather = (wardId: string) => get<any>(`/api/weather?ward_id=${wardId}`);
export const getHeatmap = () => get<any[]>("/api/heatmap");
export const getTraffic = (wardId: string) => get<any>(`/api/traffic?ward_id=${wardId}`);
export const getConstruction = (wardId: string) => get<any>(`/api/construction?ward_id=${wardId}`);

// --- Person B: forecast + source attribution ---
export const getPredict = (wardId: string, horizon = 24) =>
  get<any>(`/api/predict?ward_id=${wardId}&horizon=${horizon}`);
export const getSourceAttribution = (wardId: string) => get<any>(`/api/source-attribution?ward_id=${wardId}`);

// --- Person C: agents ---
export const getRecommend = (wardId: string) => get<any>(`/api/recommend?ward_id=${wardId}`);
export const getAdvisory = (wardId: string, lang = "en", context?: string) =>
  get<any>(`/api/advisory?ward_id=${wardId}&lang=${lang}${context ? `&context=${context}` : ""}`);
export const officerChat = (body: { message: string; ward_id?: string; session_id?: string }) =>
  post<any>("/api/chat", body);
export const getChatHistory = (sessionId: string) =>
  get<{ session_id: string; messages: any[] }>(`/api/chat/history?session_id=${sessionId}`);
