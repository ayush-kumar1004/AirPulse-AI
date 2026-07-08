# Prompt for Person C — LLM / AI Agents Engineer
Paste everything below into your AI tool (Claude for reasoning agents; GPT/Kimi for translation).

---

You are helping me build my part of a team hackathon project. Read this fully before writing any code.

## The project (what the whole team is building)
"AI-Powered Urban Air Quality Intelligence" for the ET AI Hackathon. Demo-ready prototype (not
production). ONE city only: **Delhi**. The product gives: (1) why AQI is high by source, (2) a
24/48/72h AQI forecast per ward, (3) government action advice, (4) a ward heat map, (5) a citizen
health advisor, plus an officer chat agent. My part is the AI/reasoning layer — this is the
differentiator that makes the product feel intelligent, not just a dashboard of numbers.

Data reality: AQI and weather are REAL; traffic, construction, and industrial zones are SIMULATED
with realistic rules — said openly in the demo.

## Architecture (fixed — do not change)
- ONE FastAPI backend, ONE repo, no microservices. My agents are NOT separate servers — they are
  Python functions my router calls in-process.
- The repo skeleton already exists and runs with ZERO errors. Every endpoint returns fake sample
  data now. My job is to replace the fake data in MY area with real agent logic.
- Fixed API contract. **Never change a response shape** without telling the team.

## What is already done (do not rebuild these)
- FastAPI app and all routers exist and run.
- Shared response shapes: `backend/app/models/schemas.py` (match these exactly).
- My inputs come from other people's modules — I call them IN-PROCESS (import their functions), or
  hit their endpoints:
  - Forecast (Person B): `GET /api/predict?ward=X`
  - Source breakdown (Person B): `GET /api/source-attribution?ward=X`
  - Current AQI (Person A): `GET /api/aqi?ward=X`
  - Weather (Person A): `GET /api/weather?ward=X`
  These return fake-but-correct data now, so I can build my agents before A and B finish.

## MY JOB (Person C — LLM / Agents)
Build the reasoning + communication layer with LangChain/LangGraph. I own three endpoints:

| Endpoint | Returns |
|----------|---------|
| `GET /api/recommend?ward=X` | Ranked government actions + inspection priority list |
| `GET /api/advisory?ward=X&lang=hi&context=asthma` | Personalised, multilingual citizen health advice |
| `POST /api/chat` (body: `{message, ward_id}`) | Officer chat agent reply + which tools it used |

Three agents to build:
1. **Government Action Recommendation** — takes forecast + source breakdown + ward context; returns
   specific, prioritised actions like "Restrict diesel trucks on Ring Road 6–10am". Use a strict JSON
   output schema. Map scenarios to real government levers (high traffic → restrict diesel trucks;
   high construction → halt + dust netting; high dust → water-spray roads; high industry → inspect
   factory within 24h).
2. **Citizen Health Advisor** — takes ward AQI + forecast + user context (asthma, jogger, elderly) +
   language; returns warm, plain-language advice: safe outdoor hours, mask guidance, indoor/outdoor.
   Output in the chosen language (English + Hindi + one regional language). Keep a few hardcoded
   safety facts (N95, asthma) the LLM must not contradict — treat the LLM as a communicator of vetted
   facts, not the medical source.
3. **Officer Chat Agent** — a LangGraph agent that answers questions like "Why is Zone 4 polluted
   today?" or "Which ward should inspectors visit first?" by CALLING the other modules as TOOLS (not
   hardcoded). It must report which tools it used.

Model routing: use **Claude** for the reasoning agents (recommendations, chat, source explanation).
Use **GPT or Kimi** for multilingual translation/tone in the citizen advisor, or as a fallback.

## My files (where I write code)
- `backend/app/routers/agents.py` — my 3 endpoints (replace mock returns with agent calls).
- `backend/app/llm/llm_client.py` — factory returning a LangChain chat model (Claude/GPT/Kimi).
- `backend/app/llm/tools.py` — LangChain tools that wrap A's and B's functions so the chat agent can
  call them (get_aqi, get_predict, get_source_attribution, get_weather).
- `backend/app/llm/recommendation_agent.py` — `recommend_actions(ward_id)`.
- `backend/app/llm/citizen_advisor.py` — `advise(ward_id, language, profile)`.
- `backend/app/llm/officer_chat.py` — `chat(message, ward_id)`.

## The exact data shapes I must return (from schemas.py — do not change field names)
- RecommendationResponse: `ward_id, actions[], inspection_priority[]`
  - ActionRecommendation: `action, target, urgency (high|medium|low), reason`
  - InspectionItem: `site, ward_id, reason, priority (int)`
- CitizenAdviceResponse: `ward_id, language, aqi, advice, best_outdoor_window, worst_outdoor_window`
- ChatResponse: `reply, tools_used (list)`

## How to start (in this order)
1. Read `schemas.py` for the exact output shapes.
2. Set up `llm_client.py` with Claude (put keys in `backend/.env`: `ANTHROPIC_API_KEY`, etc).
3. Build the recommendation agent first — it is the clearest win. Force strict JSON output.
4. Build the citizen advisor; test Hindi + one regional language output quality.
5. Build the tools in `tools.py`, then the officer chat agent that uses them.
6. Test the chat agent against the 4 example questions from the problem statement using live module
   data — not hardcoded answers.
7. Stretch (only if time): light RAG over 2–3 GRAP-stage rule docs so actions cite a real rule.

## Rules
- Match the shapes in `schemas.py` exactly. Message the team before any shape change.
- Only edit MY files above. Do not touch `data_ingestion/`, `ml/`, or `frontend/`.
- The chat agent must reason with real tools, not fake replies — that is the whole point.

Now help me build this one file at a time, starting with `llm_client.py` and the recommendation agent.
