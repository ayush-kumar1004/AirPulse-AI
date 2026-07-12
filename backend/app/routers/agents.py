# Person C — LLM/Agents. Owns DOCX Section 6 endpoints /api/recommend, /api/advisory, POST /api/chat.
# Real logic: app.llm.recommendation_agent, app.llm.citizen_advisor, app.llm.officer_chat.
from fastapi import APIRouter, Query

from app.llm.citizen_advisor import advise
from app.llm.officer_chat import chat as chat_agent
from app.llm.recommendation_agent import recommend_actions
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    CitizenAdviceResponse,
    RecommendationResponse,
)

router = APIRouter(prefix="/api", tags=["agents (Person C)"])


@router.get("/recommend", response_model=RecommendationResponse)
def recommend(ward_id: str = Query(...)):
    """Ranked government action list + inspection priority. Calls recommendation_agent."""
    data = recommend_actions(ward_id)
    return RecommendationResponse(**data)


@router.get("/advisory", response_model=CitizenAdviceResponse)
def advisory(
    ward_id: str = Query(...),
    lang: str = Query("en", description="en | hi | <regional>"),
    context: str | None = Query(None, description="e.g. asthma, jogger, elderly, child"),
):
    """Personalised, multilingual citizen health advisory. Calls citizen_advisor."""
    data = advise(ward_id, language=lang, profile=context)
    return CitizenAdviceResponse(**data)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Officer chat agent — answers e.g. 'why is Zone 4 polluted today?' / 'which ward first?' by calling
    other modules as tools."""
    data = chat_agent(req.message, req.ward_id)
    return ChatResponse(**data)
