# Person C — LLM/Agents. Owns DOCX Section 6 endpoints /api/recommend, /api/advisory, POST /api/chat.
# Real logic: app.llm.recommendation_agent, app.llm.citizen_advisor, app.llm.officer_chat.
import json
import logging
import time
from typing import Any

from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool

from app.llm.citizen_advisor import advise
from app.llm.officer_chat import chat as chat_agent, get_chat_history
from app.llm.recommendation_agent import recommend_actions
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CitizenAdviceResponse,
    RecommendationResponse,
)
from app.redis_client import redis_client

router = APIRouter(prefix="/api", tags=["agents (Person C)"])

logger = logging.getLogger(__name__)

# Every call here costs one LLM request, and the free Gemini tier allows only 20
# per day. Air quality moves slowly, so serving a cached answer for 30 minutes is
# both accurate enough and the difference between a working demo and a 429.
LLM_CACHE_SECONDS = 30 * 60
_IN_MEM_AGENT_CACHE: dict[str, tuple[float, Any]] = {}


async def _cached_llm(cache_key: str, fn, *args):
    """Run a blocking LLM agent off the event loop, caching its result in Memory & Redis.

    Memory cache ensures sub-millisecond response even without external Redis.
    """
    cached_mem = _IN_MEM_AGENT_CACHE.get(cache_key)
    if cached_mem and (time.monotonic() - cached_mem[0] < LLM_CACHE_SECONDS):
        return cached_mem[1]

    try:
        cached = await redis_client.get(cache_key)
        if cached:
            parsed = json.loads(cached)
            _IN_MEM_AGENT_CACHE[cache_key] = (time.monotonic(), parsed)
            return parsed
    except Exception:
        logger.warning("Cache read failed for %s — calling the model.", cache_key, exc_info=False)

    data = await run_in_threadpool(fn, *args)

    _IN_MEM_AGENT_CACHE[cache_key] = (time.monotonic(), data)
    try:
        await redis_client.setex(cache_key, LLM_CACHE_SECONDS, json.dumps(data, default=str))
    except Exception:
        pass

    return data


@router.get("/recommend", response_model=RecommendationResponse)
async def recommend(ward_id: str = Query(...)):
    """Ranked government action list + inspection priority. Calls recommendation_agent."""
    data = await _cached_llm(f"recommend:{ward_id}", recommend_actions, ward_id)
    return RecommendationResponse(**data)


@router.get("/advisory", response_model=CitizenAdviceResponse)
async def advisory(
    ward_id: str = Query(...),
    lang: str = Query("en", description="en | hi | <regional>"),
    context: str | None = Query(None, description="e.g. asthma, jogger, elderly, child"),
):
    """Personalised, multilingual citizen health advisory. Calls citizen_advisor."""
    data = await _cached_llm(f"advisory:{ward_id}:{lang}:{context or ''}", advise, ward_id, lang, context)
    return CitizenAdviceResponse(**data)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Officer chat agent — answers e.g. 'why is Zone 4 polluted today?' / 'which ward first?' by calling
    other modules as tools with multi-turn session memory."""
    # Not cached: each question is different, and a repeated question should get a
    # fresh answer against current conditions.
    data = await run_in_threadpool(chat_agent, req.message, req.ward_id, req.session_id)
    return ChatResponse(**data)


@router.get("/chat/history")
async def chat_history(session_id: str = Query(...)):
    """Retrieve persistent conversation history for an officer session from the checkpointer."""
    messages = await run_in_threadpool(get_chat_history, session_id)
    return {"session_id": session_id, "messages": messages}


@router.get("/regulations/search")
async def search_regulations_endpoint(
    query: str = Query(..., description="Query for statutory air regulations"),
    top_k: int = Query(5, ge=1, le=10),
    category: str | None = Query(None, description="Optional category filter e.g. GRAP_STAGE_3, AIR_ACT_1981"),
):
    """Semantic vector search across GRAP, CAQM Directions, and Air Act 1981."""
    from app.rag.vector_store import similarity_search_db
    results = await similarity_search_db(query=query, top_k=top_k, category=category)
    return {"query": query, "total_matches": len(results), "results": results}


@router.get("/simulate")
async def simulate_endpoint(
    ward_id: str = Query("CANT_1", description="Ward ID or 'citywide'"),
    intervention: str = Query("construction_ban", description="Intervention type e.g. construction_ban, diesel_truck_ban, odd_even"),
    intensity: float = Query(1.0, ge=0.1, le=1.0),
    horizon: int = Query(24, ge=12, le=72),
):
    """Run What-If Policy Intervention Simulation coupling Source Attribution with LightGBM."""
    from app.ml.intervention_simulator import simulate_ward_intervention, simulate_citywide_intervention
    if ward_id.lower() in ("citywide", "all"):
        return simulate_citywide_intervention(intervention, intensity, horizon)
    return simulate_ward_intervention(ward_id, intervention, intensity, horizon)


@router.get("/observability/telemetry")
async def telemetry_endpoint(
    limit: int = Query(50, ge=1, le=200),
    event_type: str | None = Query(None, description="Optional filter: ml_forecast_inference, agent_tool_call, rag_retrieval, policy_simulation, model_evaluation"),
):
    """Inspect structured runtime telemetry events, tool calls, and model inference metrics."""
    from app.observability import get_recent_telemetry_events
    events = get_recent_telemetry_events(limit=limit, event_type=event_type)
    return {"total_events": len(events), "events": events}


