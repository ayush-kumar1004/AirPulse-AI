# SHARED Pydantic response schemas — the API contract (DOCX Section 6, the single source of truth).
# RULE: nobody changes a response shape after Day 2 without messaging the whole team.
# These shapes MUST match what routers return (mock or real).
from typing import Optional

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Person A — data
# ---------------------------------------------------------------------------


class WardAQI(BaseModel):
    """GET /api/aqi?ward=X — current AQI + pollutant breakdown for one ward."""
    ward_id: str
    ward_name: str
    aqi: int
    category: str            # CPCB: good | satisfactory | moderate | poor | very_poor | severe
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no2: Optional[float] = None
    updated_at: str


class HeatmapWard(BaseModel):
    """GET /api/heatmap — one entry per ward, just enough to colour the map."""
    ward_id: str
    ward_name: str
    aqi: int
    category: str


class TrafficSignal(BaseModel):
    """GET /api/traffic?ward=X — SIMULATED traffic density (rules-based)."""
    ward_id: str
    traffic_index: float     # 0..1, rush-hour weighted
    note: str = "SIMULATED — rules-based, not live data"


class ConstructionSignal(BaseModel):
    """GET /api/construction?ward=X — SIMULATED active construction sites (rules-based)."""
    ward_id: str
    active_sites: int
    site_names: list[str] = []
    note: str = "SIMULATED — rules-based, seeded with known project locations"


# ---------------------------------------------------------------------------
# Person B — forecast + source attribution
# ---------------------------------------------------------------------------


class ForecastPoint(BaseModel):
    timestamp: str
    predicted_aqi: int
    trend: str               # rising | falling | stable
    lower: Optional[int] = None
    upper: Optional[int] = None


class ForecastResponse(BaseModel):
    """GET /api/predict?ward=X — 24/48/72h AQI forecast array."""
    ward_id: str
    horizon_hours: int       # 24 | 48 | 72
    points: list[ForecastPoint]
    model: str               # "prophet" | "xgboost" | "mock"


class SourceBreakdown(BaseModel):
    """GET /api/source-attribution?ward=X — % breakdown by source + confidence + raw factors."""
    ward_id: str
    traffic: float           # 0..1 share (all four sum to ~1.0)
    construction: float
    industry: float
    dust: float
    confidence: float        # 0..1 (lower when a driving signal is simulated)
    raw_factors: dict = {}   # the pre-normalised signals, for transparency
    reasoning: str           # one-paragraph plain-language explanation


# ---------------------------------------------------------------------------
# Person C — agents
# ---------------------------------------------------------------------------


class ActionRecommendation(BaseModel):
    """One government intervention. DOCX schema: {action, target, urgency, reason}."""
    action: str
    target: str              # named zone / road / factory
    urgency: str             # high | medium | low
    reason: str


class InspectionItem(BaseModel):
    site: str
    ward_id: str
    reason: str
    priority: int            # 1 = visit first


class RecommendationResponse(BaseModel):
    """GET /api/recommend?ward=X — ranked actions + inspection priority list."""
    ward_id: str
    actions: list[ActionRecommendation]
    inspection_priority: list[InspectionItem] = []


class CitizenAdviceResponse(BaseModel):
    """GET /api/advisory?ward=X&lang=hi&context=asthma — personalised health guidance."""
    ward_id: str
    language: str
    aqi: int
    advice: str
    best_outdoor_window: Optional[str] = None
    worst_outdoor_window: Optional[str] = None


class ChatRequest(BaseModel):
    """POST /api/chat body."""
    message: str
    ward_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str] = []
