# AirIntel — AI-Powered Urban Air Quality Intelligence

ET AI Hackathon Round 2 · Single-city prototype (**Delhi** by default — swap via `CITY` env var).

A **single FastAPI backend + single React frontend**, one repo, no microservices. Every AI
module is a plain Python function called in-process by its owner's router. The frontend talks to
**exactly one backend URL** through **one shared API client**.

---

## What it does (5 modules + 1 agent)

| # | Module | Owner | What it does |
|---|--------|-------|--------------|
| 1 | Pollution Source Detection | Person B | Transparent weighted-scoring model → % breakdown (traffic/construction/industry/dust) + confidence |
| 2 | AQI Prediction | Person B | 24/48/72h per-ward forecast (Prophet, XGBoost fallback) on real AQI + weather |
| 3 | Govt Action Recommendation | Person C | Claude agent turns forecast + sources into specific prioritised actions |
| 4 | Pollution Heat Map | Person D | Interactive ward-level map, green→dark-red, clickable |
| 5 | Citizen Health Advisor | Person C | Multilingual (EN/HI/+1) personalised health guidance |
| + | Officer Chat Agent | Person C | Answers "why is Zone 4 polluted today?" by calling the other modules as tools |

**Data reality:** AQI (OpenAQ/CPCB) + weather (Open-Meteo) are **real**. Traffic, construction,
and industrial-zone signals are **simulated** with rules-based patterns — stated openly in the demo.

---

## Repo layout & ownership

```
.
├── backend/                  # ONE FastAPI app
│   ├── main.py               # imports all routers — runs clean from commit #1
│   ├── app/
│   │   ├── config.py         # shared — settings/env
│   │   ├── database.py       # Person A — Postgres + PostGIS
│   │   ├── redis_client.py   # Person A — Redis cache
│   │   ├── routers/          # one router file per owner (all serve /api/* per the contract)
│   │   │   ├── health.py     # shared — liveness
│   │   │   ├── data.py       # Person A — /api/wards /aqi /weather /heatmap /traffic /construction
│   │   │   ├── forecast.py   # Person B — /api/predict
│   │   │   ├── sources.py    # Person B — /api/source-attribution
│   │   │   └── agents.py     # Person C — /api/recommend /advisory /chat
│   │   ├── models/           # Person A — SQLAlchemy tables + shared Pydantic schemas
│   │   ├── data_ingestion/   # Person A — AQI/weather ingest, synthetic gen, ward loader
│   │   ├── ml/               # Person B — forecast_model.py, source_attribution.py
│   │   ├── llm/              # Person C — agents + LangChain tools + LLM client
│   │   └── data/             # ward GeoJSON + seed files
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                 # React + TS + Tailwind (Vite)
│   ├── src/
│   │   ├── api/client.ts     # Person D — THE single shared API client
│   │   ├── components/       # Person D — HeatMap, WardPanel, charts, chat, RecommendationPanel
│   │   └── pages/            # Person D — the 5 screens (below)
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml        # postgres+postgis, redis, backend, frontend
└── README.md
```

| Folder | Owner | Role |
|--------|-------|------|
| `backend/app/data_ingestion`, `models`, `database.py`, `redis_client.py`, `routers/data.py` | **Person A** | Data & Backend |
| `backend/app/ml`, `routers/forecast.py`, `routers/sources.py` | **Person B** | ML / Forecasting |
| `backend/app/llm`, `routers/agents.py` | **Person C** | LLM / Agents |
| `frontend/` | **Person D** | Frontend |

---

## API contract (DOCX Section 6 — the single source of truth)

**Rule: nobody changes a response shape after Day 2 without messaging the whole team.**
Frontend pages: City Dashboard `/`, Pollution Map `/map`, Forecast `/forecast`, Government `/government`, Citizen `/citizen`.

| Method | Path | Owner | Returns |
|--------|------|-------|---------|
| GET | `/health` | shared | Liveness + city/env |
| GET | `/api/wards` | A | Ward GeoJSON polygons + metadata |
| GET | `/api/aqi?ward=X` | A | Current AQI + pollutant breakdown for a ward |
| GET | `/api/weather?ward=X` | A | Current + forecast weather for a ward |
| GET | `/api/heatmap` | A | Per-ward AQI snapshot for map colouring (all wards) |
| GET | `/api/traffic?ward=X` | A | Simulated traffic density score |
| GET | `/api/construction?ward=X` | A | Simulated active construction sites |
| GET | `/api/predict?ward=X&horizon=24\|48\|72` | B | 24/48/72h AQI forecast array |
| GET | `/api/source-attribution?ward=X` | B | % breakdown by source + confidence + raw factors |
| GET | `/api/recommend?ward=X` | C | Ranked government actions + inspection priority |
| GET | `/api/advisory?ward=X&lang=hi&context=asthma` | C | Citizen health advisory (multilingual) |
| POST | `/api/chat` | C | Officer chat agent response (tool-using) |

---

## Run it

### Option A — Docker (everything at once)
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```
- Backend → http://localhost:8000  (docs at `/docs`)
- Frontend → http://localhost:5173
- Postgres → localhost:5432 · Redis → localhost:6379

### Option B — local dev (backend)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

### Option B — local dev (frontend)
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The app runs **green from commit #1** — every endpoint returns mock data until its owner fills in
real logic, so no one is ever blocked waiting on someone else.

---

## Working agreement
- One shared branch model: `main` (protected) ← feature branches `feat/<area>-<name>`.
- Don't edit another person's folder without a heads-up. Shared files (`config.py`,
  `models/schemas.py`, `main.py`, `api/client.ts`) change only by agreement.
- Keep the mock return shapes in each stub as the **contract** — match them when you add real logic
  so the frontend never breaks.
