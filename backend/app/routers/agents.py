# TODO: Person C — LLM/Agents. Owns DOCX Section 6 endpoints /api/recommend, /api/advisory, POST /api/chat.
# Returns MOCK now; swap for app.llm.*. The chat agent must call other modules as TOOLS (not hardcode).
from fastapi import APIRouter, Query

from app.models.schemas import (
    ActionRecommendation,
    ChatRequest,
    ChatResponse,
    CitizenAdviceResponse,
    InspectionItem,
    RecommendationResponse,
)

router = APIRouter(prefix="/api", tags=["agents (Person C)"])


@router.get("/recommend", response_model=RecommendationResponse)
def recommend(ward: str = Query(..., description="ward_id")):
    """Ranked government action list + inspection priority. TODO: Person C — app.llm.recommendation_agent,
    fed forecast (Person B) + source attribution (Person B). Strict JSON out, mapped to real govt levers."""
    return RecommendationResponse(
        ward_id=ward,
        actions=[
            ActionRecommendation(action="Restrict diesel trucks on Ring Road 06:00-10:00",
                                 target="Ring Road corridor", urgency="high",
                                 reason="Traffic is 45% of load with a rising forecast tomorrow AM."),
            ActionRecommendation(action="Halt open construction & mandate dust netting + water spraying",
                                 target=f"Ward {ward}", urgency="medium",
                                 reason="Two active sites contribute 25%; dry, low-wind conditions."),
        ],
        inspection_priority=[
            InspectionItem(site="Metro Phase-4 site", ward_id=ward, reason="Largest active dust source", priority=1),
        ],
    )


@router.get("/advisory", response_model=CitizenAdviceResponse)
def advisory(
    ward: str = Query(..., description="ward_id"),
    lang: str = Query("en", description="en | hi | <regional>"),
    context: str | None = Query(None, description="e.g. asthma, jogger, elderly, child"),
):
    """Personalised, multilingual citizen health advisory. TODO: Person C — app.llm.citizen_advisor.
    Keep hardcoded safety facts (N95, asthma) the LLM must not contradict."""
    return CitizenAdviceResponse(
        ward_id=ward,
        language=lang,
        aqi=182,
        advice="AQI is 'poor' today. If you have asthma, avoid outdoor jogging before noon and wear an N95 mask.",
        best_outdoor_window="15:00-17:00",
        worst_outdoor_window="07:00-10:00",
    )


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Officer chat agent — answers e.g. 'why is Zone 4 polluted today?' / 'which ward first?' by calling
    other modules as tools. TODO: Person C — app.llm.officer_chat (LangGraph, tools = aqi/predict/source/recommend)."""
    return ChatResponse(
        reply="Zone 4 AQI is 241 (severe). Main driver: traffic (45%). Forecast stays severe through tomorrow "
              "morning, so it's the top inspection priority.",
        tools_used=["get_aqi", "get_source_attribution", "get_predict"],
    )
