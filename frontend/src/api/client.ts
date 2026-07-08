// THE single shared API client. Owner: Person D. Change only by team agreement.
// Paths mirror the DOCX Section 6 contract EXACTLY. Never fetch a backend URL directly elsewhere.

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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
export const getWards = () => get<any>("/api/wards");
export const getAQI = (ward: string) => get<any>(`/api/aqi?ward=${ward}`);
export const getWeather = (ward: string) => get<any>(`/api/weather?ward=${ward}`);
export const getHeatmap = () => get<any[]>("/api/heatmap");
export const getTraffic = (ward: string) => get<any>(`/api/traffic?ward=${ward}`);
export const getConstruction = (ward: string) => get<any>(`/api/construction?ward=${ward}`);

// --- Person B: forecast + source attribution ---
export const getPredict = (ward: string, horizon = 24) =>
  get<any>(`/api/predict?ward=${ward}&horizon=${horizon}`);
export const getSourceAttribution = (ward: string) => get<any>(`/api/source-attribution?ward=${ward}`);

// --- Person C: agents ---
export const getRecommend = (ward: string) => get<any>(`/api/recommend?ward=${ward}`);
export const getAdvisory = (ward: string, lang = "en", context?: string) =>
  get<any>(`/api/advisory?ward=${ward}&lang=${lang}${context ? `&context=${context}` : ""}`);
export const officerChat = (body: { message: string; ward_id?: string }) =>
  post<any>("/api/chat", body);
