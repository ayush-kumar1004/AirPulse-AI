# Prompt for Person A — Data & Backend Engineer
Paste everything below into your AI tool (Antigravity for scaffolding, Claude for logic/debugging).

---

You are helping me build my part of a team hackathon project. Read this fully before writing any code.

## The project (what the whole team is building)
"AI-Powered Urban Air Quality Intelligence" for the ET AI Hackathon. It is a demo-ready prototype
(not a production system). We build for ONE city only: **Delhi** (best AQI station data).
The product sits on top of air-quality data and gives: (1) why AQI is high broken down by source,
(2) a 24/48/72h AQI forecast per ward, (3) government action advice, (4) a colour-coded ward heat map,
(5) a citizen health advisor, plus an officer chat agent.

Data reality: AQI (OpenAQ/CPCB) and weather (Open-Meteo) are REAL. Traffic, construction, and
industrial zones are SIMULATED with realistic rules — we say this openly in the demo.

## Architecture (fixed — do not change)
- ONE FastAPI backend, ONE repo, no microservices. Each person owns router files and module code
  that runs in-process.
- The repo skeleton already exists and runs with ZERO errors. Every endpoint currently returns
  fake sample data. My job is to replace the fake data in MY area with real logic.
- There is a fixed API contract. **Never change a response shape** without telling the team — the
  frontend depends on these exact shapes.

## What is already done (do not rebuild these)
- FastAPI app: `backend/main.py` (loads all routers, CORS set once).
- Shared settings: `backend/app/config.py` (reads `.env`, has `CITY`, `DATABASE_URL`, `REDIS_URL`,
  `OPENAQ_API_KEY`, etc).
- Shared response shapes: `backend/app/models/schemas.py` (the contract — match these exactly).
- Empty stubs waiting for my code (see "My files" below).
- `docker-compose.yml` already defines Postgres+PostGIS and Redis.

## MY JOB (Person A — Data & Backend)
Get every data source flowing into a shared database that B, C, and D can query. Everyone depends on
me, so I go first. I own these endpoints (all live under `backend/app/routers/data.py`):

| Endpoint | Returns |
|----------|---------|
| `GET /api/wards` | Ward polygons as GeoJSON + metadata |
| `GET /api/aqi?ward=X` | Current AQI + pollutant breakdown for one ward |
| `GET /api/weather?ward=X` | Current + forecast weather for a ward (Open-Meteo) |
| `GET /api/heatmap` | AQI for ALL wards (used to colour the map) |
| `GET /api/traffic?ward=X` | Simulated traffic score (rules-based) |
| `GET /api/construction?ward=X` | Simulated active construction sites |

## My files (where I write code)
- `backend/app/routers/data.py` — my API endpoints (replace the mock returns with real calls).
- `backend/app/database.py` — Postgres + PostGIS connection (SQLAlchemy engine/session/Base).
- `backend/app/redis_client.py` — Redis cache helpers (already has `cache_get`/`cache_set`).
- `backend/app/models/db_models.py` — my database tables (wards, aqi_readings, weather, signals).
- `backend/app/data_ingestion/aqi_ingest.py` — pull real AQI from OpenAQ/CPCB.
- `backend/app/data_ingestion/weather_ingest.py` — pull real weather from Open-Meteo (no key needed).
- `backend/app/data_ingestion/synthetic.py` — rules-based traffic/construction/industry generator.
- `backend/app/data_ingestion/wards.py` — load ward GeoJSON into PostGIS.
- `backend/app/data/wards.geojson` — replace the 2 placeholder wards with REAL Delhi ward boundaries.
- `backend/app/data/industrial_zones.geojson` — static overlay of known industrial areas.

## The exact data shapes I must return (from schemas.py — do not change field names)
- WardAQI: `ward_id, ward_name, aqi (int), category (good|satisfactory|moderate|poor|very_poor|severe),
  pm25, pm10, no2, updated_at`
- HeatmapWard: `ward_id, ward_name, aqi, category`
- TrafficSignal: `ward_id, traffic_index (0..1), note`
- ConstructionSignal: `ward_id, active_sites (int), site_names (list), note`

## How to start (in this order)
1. Read `backend/app/models/schemas.py` so you know the exact shapes to return.
2. Build `weather_ingest.py` first — Open-Meteo is free and needs no key. Return current + forecast.
3. Then `aqi_ingest.py` — get an OpenAQ API key, pull latest + 6–12 months history for Delhi.
4. Get real Delhi ward GeoJSON (OpenStreetMap / city open data), load it via `wards.py`.
5. Set up the database tables in `db_models.py`, run PostGIS, store history.
6. Build the synthetic generator: traffic peaks at 8–10am & 6–8pm on weekdays; construction sites
   active in daytime; keep it deterministic per (ward, hour) so the demo repeats the same.
7. Cache `/api/heatmap` and `/api/aqi` in Redis (they are hit a lot).

## Rules
- Match the response shapes in `schemas.py` exactly. If a shape must change, message the whole team first.
- Only edit MY files listed above. Do not touch `ml/`, `llm/`, or `frontend/`.
- Goal: no fake data left in my endpoints. Real, correctly-shaped JSON that B/C/D can call.

Now help me build these one file at a time, starting with `weather_ingest.py`.
