# Prompt for Person D — Frontend Engineer
Paste everything below into your AI tool (Stitch for layouts; Claude/Antigravity for wiring).

---

You are helping me build my part of a team hackathon project. Read this fully before writing any code.

## The project (what the whole team is building)
"AI-Powered Urban Air Quality Intelligence" for the ET AI Hackathon. Demo-ready prototype (not
production). ONE city only: **Delhi**. The product gives: (1) why AQI is high by source, (2) a
24/48/72h AQI forecast per ward, (3) government action advice, (4) a colour-coded ward heat map,
(5) a citizen health advisor, plus an officer chat agent. My job is the frontend — make the
intelligence visible and impressive to judges within 10 seconds of opening the app.

Data reality: AQI and weather are REAL; traffic, construction, and industrial zones are SIMULATED
with realistic rules — said openly in the demo.

## Architecture (fixed — do not change)
- ONE FastAPI backend, ONE repo. The frontend talks to EXACTLY ONE backend URL through ONE shared
  API client file. Never call the backend directly from a component — always go through the client.
- The repo skeleton already exists and runs with ZERO errors. Every backend endpoint returns fake
  sample data now, so I can build ALL screens immediately without waiting for A, B, or C.
- Fixed API contract. The client function names/paths already match it — do not change paths.

## What is already done (do not rebuild these)
- Frontend app set up: React + TypeScript + Vite + Tailwind + Material UI.
- The single shared API client: `frontend/src/api/client.ts` (all backend calls live here).
- Router + nav with the 5 screens wired in `frontend/src/App.tsx`.
- Empty page + component stubs waiting for my UI (see "My files" below).
- `frontend/.env.example` has `VITE_API_BASE_URL` (the one backend URL) and `VITE_MAP_STYLE_URL`.

## MY JOB (Person D — Frontend)
Build the 5 screens and wire them to the backend via the shared client. Use Stitch to generate the
layout for each screen, then hand-wire the generated design into working React components (do NOT let
Stitch handle logic or state — export the look, then wire the data myself).

The 5 screens:
| Screen | Route | Shows | Uses |
|--------|-------|-------|------|
| City Dashboard | `/` | Current AQI, predicted AQI, trend chart, mini heatmap | heatmap, aqi, predict |
| Pollution Map | `/map` | Full interactive ward map + overlay toggle, click ward → side panel | wards, heatmap, aqi, predict, source |
| Forecast | `/forecast` | 24/48/72h charts + trend lines | predict |
| Government Dashboard | `/government` | Recommended actions, inspection priority list, officer chat | recommend, chat |
| Citizen View | `/citizen` | AQI, personal advisory, best/worst outdoor times, language picker | advisory |

Key pieces:
- **Heat map** (Leaflet — free, no key — or Mapbox GL). Colour each ward polygon on CPCB categories:
  green (good) → yellow (moderate) → red (poor) → dark red (severe). Click a ward → side panel.
- **Overlay toggle** on the map: current AQI / predicted +24h / dominant source (one toggle shows
  three modules — very effective in the live demo).
- **Charts** with Recharts (forecast lines with a confidence band).
- **Officer chat** panel (send message → show reply + which tools it used).
- **Citizen view** is mobile-first and simple — one screen, no navigation, language selector.

## My files (where I write code)
- `frontend/src/api/client.ts` — the shared client (already written; add functions only by team
  agreement). Available functions: `getWards, getAQI(ward), getWeather(ward), getHeatmap,
  getTraffic(ward), getConstruction(ward), getPredict(ward, horizon), getSourceAttribution(ward),
  getRecommend(ward), getAdvisory(ward, lang, context), officerChat({message, ward_id})`.
- `frontend/src/pages/` — `CityDashboard.tsx, PollutionMap.tsx, ForecastScreen.tsx,
  GovernmentDashboard.tsx, CitizenView.tsx`.
- `frontend/src/components/` — `HeatMap.tsx, WardPanel.tsx, ForecastChart.tsx, SourceBreakdown.tsx,
  OfficerChat.tsx, CitizenAdvisor.tsx, RecommendationPanel.tsx`.

## The data shapes I will receive (match these when reading responses)
- `/api/heatmap` → `[{ward_id, ward_name, aqi, category}]`
- `/api/aqi?ward=X` → `{ward_id, ward_name, aqi, category, pm25, pm10, no2, updated_at}`
- `/api/predict?ward=X&horizon=24` → `{ward_id, horizon_hours, points:[{timestamp, predicted_aqi, trend, lower, upper}], model}`
- `/api/source-attribution?ward=X` → `{ward_id, traffic, construction, industry, dust, confidence, raw_factors, reasoning}`
- `/api/recommend?ward=X` → `{ward_id, actions:[{action, target, urgency, reason}], inspection_priority:[{site, ward_id, reason, priority}]}`
- `/api/advisory?ward=X&lang=hi&context=asthma` → `{ward_id, language, aqi, advice, best_outdoor_window, worst_outdoor_window}`
- `POST /api/chat` `{message, ward_id}` → `{reply, tools_used}`

## How to start
1. Run the app: `cd frontend`, `npm install`, `cp .env.example .env`, `npm run dev` (needs the
   backend running too: `cd backend && uvicorn main:app --reload`).
2. Everything returns fake data already — so build the FULL UI now against that fake data.
3. Build the Pollution Map first — it is the biggest "wow" for judges. Then City Dashboard, Forecast,
   Government Dashboard, Citizen View.
4. Use the AQI colour scale in `tailwind.config.js` (`aqi.good/moderate/poor/severe`).
5. As A/B/C replace fake data with real data, my screens keep working because the shapes stay the same.

## Rules
- Only call the backend through `client.ts` — never `fetch()` a URL directly in a component.
- Do not change endpoint paths or response field names — those are the fixed team contract.
- Goal: all 5 screens run on real backend data with no visible fake/placeholder content by Day 12,
  and the app must not visually break on a laptop screen share (that is how judges see it).

Now help me build this one screen at a time, starting with the Pollution Map and its heat map.
