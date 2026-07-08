# Prompt for Person B — Machine Learning / Forecasting Engineer
Paste everything below into your AI tool (Claude is best for model logic and reasoning code).

---

You are helping me build my part of a team hackathon project. Read this fully before writing any code.

## The project (what the whole team is building)
"AI-Powered Urban Air Quality Intelligence" for the ET AI Hackathon. It is a demo-ready prototype
(not production). We build for ONE city only: **Delhi**. The product gives: (1) why AQI is high by
source, (2) a 24/48/72h AQI forecast per ward, (3) government action advice, (4) a ward heat map,
(5) a citizen health advisor, plus an officer chat agent.

Data reality: AQI (OpenAQ/CPCB) and weather (Open-Meteo) are REAL. Traffic, construction, and
industrial zones are SIMULATED with realistic rules — said openly in the demo.

## Architecture (fixed — do not change)
- ONE FastAPI backend, ONE repo, no microservices. My model is NOT a separate server — it is plain
  Python functions that my router calls in-process.
- The repo skeleton already exists and runs with ZERO errors. Every endpoint returns fake sample
  data now. My job is to replace the fake data in MY area with real logic.
- Fixed API contract. **Never change a response shape** without telling the team.

## What is already done (do not rebuild these)
- FastAPI app and all routers exist and run.
- Shared response shapes: `backend/app/models/schemas.py` (match these exactly).
- Person A owns the DATA. I get my inputs by calling Person A's functions/endpoints:
  - AQI history + current: Person A's ingestion / `GET /api/aqi?ward=X`
  - Weather (incl. forecast): `GET /api/weather?ward=X`
  - Simulated traffic: `GET /api/traffic?ward=X`
  - Simulated construction: `GET /api/construction?ward=X`
  - Industrial zones overlay: `backend/app/data/industrial_zones.geojson`
  My stubs currently return fake data so the app never breaks while A finishes the real data.

## MY JOB (Person B — ML / Forecasting)
Turn raw data into predictions and explanations. I own two endpoints:

| Endpoint | Returns |
|----------|---------|
| `GET /api/predict?ward=X&horizon=24\|48\|72` | AQI forecast points for the next 24/48/72h |
| `GET /api/source-attribution?ward=X` | % breakdown by source + confidence + reasoning factors |

Two things to build:
1. **AQI Forecast** — start with Facebook Prophet (fast, handles seasonality). If time allows in
   week 2, upgrade to XGBoost with lag + weather features. Train on 6–12 months of Delhi AQI history.
2. **Source Attribution** — a TRANSPARENT weighted-scoring model (NOT a black-box classifier). Take
   traffic %, construction activity, industrial proximity, wind direction, and dust/weather; output a
   percentage split across traffic/construction/industry/dust that sums to ~1.0, plus a confidence
   score. Adjust with wind (wind from an industrial zone raises the industry score; calm air lets
   local traffic/construction dominate). Lower confidence when a driving signal is simulated.

## My files (where I write code)
- `backend/app/routers/forecast.py` — the `/api/predict` endpoint (replace mock with `predict()`).
- `backend/app/routers/sources.py` — the `/api/source-attribution` endpoint (replace mock with `attribute()`).
- `backend/app/ml/forecast_model.py` — `predict(ward_id, horizon_hours)` and `train(ward_id)`.
- `backend/app/ml/source_attribution.py` — `attribute(ward_id)`; starter `WEIGHTS` dict is already there.

## The exact data shapes I must return (from schemas.py — do not change field names)
- ForecastResponse: `ward_id, horizon_hours, points[], model ("prophet"|"xgboost"|"mock")`
  - ForecastPoint: `timestamp, predicted_aqi (int), trend (rising|falling|stable), lower, upper`
- SourceBreakdown: `ward_id, traffic, construction, industry, dust (each 0..1), confidence (0..1),
  raw_factors (dict), reasoning (text)`

## How to start (in this order)
1. Read `schemas.py` so you know the exact output shapes.
2. Collect + clean 6–12 months of Delhi AQI history (ask Person A / OpenAQ / data.gov.in).
3. Build the Prophet forecast first — get a working `/api/predict` end-to-end before improving it.
4. Backtest on a real past high-AQI day (e.g. a Diwali or crop-burning week) — this becomes our demo line.
5. Build the source-attribution weighted score. Test that it moves sensibly: high wind lowers dust;
   weekday rush hour raises traffic.
6. If short on time: hardcode the category weights — a clear rules engine is a better demo than an
   opaque model, because I can explain every number to judges.

## Rules
- Match the shapes in `schemas.py` exactly. Message the team before any shape change.
- Only edit MY files above. Do not touch `data_ingestion/`, `llm/`, or `frontend/`.
- Note the source-attribution `reasoning` text can be short; Person C's LLM turns raw numbers into
  the final polished explanation for the UI.

Now help me build this one file at a time, starting with the Prophet forecast in `forecast_model.py`.
