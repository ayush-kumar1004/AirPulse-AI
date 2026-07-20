# Person C — LLM/Agents. Owns DOCX Section 6 endpoints /api/recommend, /api/advisory, POST /api/chat.
# Real logic: app.llm.recommendation_agent, app.llm.citizen_advisor, app.llm.officer_chat.
import json
import logging

from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool

from app.llm.citizen_advisor import advise
from app.llm.officer_chat import chat as chat_agent
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


async def _cached_llm(cache_key: str, fn, *args):
    """Run a blocking LLM agent off the event loop, caching its result in Redis.

    Redis problems are logged and ignored — a cache outage must not take the
    endpoint down with it.
    """
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        logger.warning("Cache read failed for %s — calling the model.", cache_key, exc_info=True)

    data = await run_in_threadpool(fn, *args)

    try:
        await redis_client.setex(cache_key, LLM_CACHE_SECONDS, json.dumps(data, default=str))
    except Exception:
        logger.warning("Cache write failed for %s.", cache_key, exc_info=True)

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
    other modules as tools."""
    # Not cached: each question is different, and a repeated question should get a
    # fresh answer against current conditions.
    data = await run_in_threadpool(chat_agent, req.message, req.ward_id)
    return ChatResponse(**data)
