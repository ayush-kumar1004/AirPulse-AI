# Person C — LLM/Agents. Owns DOCX Section 6 endpoints /api/recommend, /api/advisory, POST /api/chat.
from fastapi import APIRouter, Query

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CitizenAdviceResponse,
    RecommendationResponse,
)
from app.llm.recommendation_agent import recommend_actions
from app.llm.citizen_advisor import advise
from app.llm.officer_chat import chat as chat_agent

router = APIRouter(prefix="/api", tags=["agents (Person C)"])


@router.get("/recommend", response_model=RecommendationResponse)
def recommend(ward: str = Query(..., description="ward_id")):
    """Ranked government action list + inspection priority. Calls recommendation_agent."""
    data = recommend_actions(ward)
    return RecommendationResponse(**data)


@router.get("/advisory", response_model=CitizenAdviceResponse)
def advisory(
    ward: str = Query(..., description="ward_id"),
    lang: str = Query("en", description="en | hi | <regional>"),
    context: str | None = Query(None, description="e.g. asthma, jogger, elderly, child"),
):
    """Personalised, multilingual citizen health advisory. Calls citizen_advisor."""
    data = advise(ward, language=lang, profile=context)
    return CitizenAdviceResponse(**data)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Officer chat agent — answers e.g. 'why is Zone 4 polluted today?' / 'which ward first?' by calling
    other modules as tools."""
    data = chat_agent(req.message, req.ward_id)
    return ChatResponse(**data)

