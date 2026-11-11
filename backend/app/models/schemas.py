# SHARED Pydantic response schemas — the API contract (DOCX Section 6, the single source of truth).
# RULE: nobody changes a response shape after Day 2 without messaging the whole team.
# These shapes MUST match what routers return (mock or real).
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Person A — data
# ---------------------------------------------------------------------------


class WardMetadata(BaseModel):
    """
    Metadata about a specific ward in the city.
    """
    ward_id: str = Field(..., description="Unique identifier for the ward")
    name: str = Field(..., description="Name of the ward")
    area_sqkm: float = Field(..., description="Area of the ward in square kilometers")
    population: Optional[int] = Field(None, description="Estimated population of the ward")


class WardAQI(BaseModel):
    """
    AQI information for a specific ward matching the API contract.
    """
    ward_id: str = Field(..., description="Unique identifier for the ward")
    ward_name: str = Field(..., description="Name of the ward")
    aqi: int = Field(..., description="Overall Air Quality Index value")
    category: str = Field(..., description="AQI Category (e.g. Good, Moderate, Severe)")
    pm25: float = Field(..., description="PM2.5 concentration")
    pm10: float = Field(..., description="PM10 concentration")
    no2: float = Field(..., description="NO2 concentration")
    updated_at: datetime = Field(..., description="Time the reading was last updated")


class HeatmapWard(BaseModel):
    """
    Simplified ward data tailored for rendering the pollution heatmap on the frontend.
    """
    ward_id: str = Field(..., description="Unique identifier for the ward")
    ward_name: str = Field(..., description="Name of the ward")
    aqi: int = Field(..., description="Current AQI value for color coding")
    category: str = Field(..., description="AQI Category (e.g. Good, Moderate, Severe)")


class TrafficSignal(BaseModel):
    """
    Simulated traffic density data for a ward.
    """
    ward_id: str = Field(..., description="Unique identifier for the ward")
    traffic_index: float = Field(..., ge=0.0, le=1.0, description="Traffic index score between 0.0 and 1.0")
    note: str = Field(..., description="Additional context or notes about the traffic")


class ConstructionSignal(BaseModel):
    """
    Simulated construction activity data for a ward.
    """
    ward_id: str = Field(..., description="Unique identifier for the ward")
    active_sites: int = Field(..., description="Number of active construction sites in the ward")
    site_names: List[str] = Field(..., description="List of names of active construction sites")
    note: str = Field(..., description="Additional context or notes about the construction")


class WeatherResponse(BaseModel):
    """
    Weather data for a given location, combining current conditions and forecasts.
    """
    ward_id: str = Field(..., description="Unique identifier for the ward")
    timestamp: datetime = Field(..., description="Time of the weather reading")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Relative humidity percentage")
    wind_speed: float = Field(..., description="Wind speed in km/h")
    wind_direction: float = Field(..., description="Wind direction in degrees")
    precipitation: float = Field(..., description="Precipitation in mm")


class AQIHistoryRecord(BaseModel):
    """
    Historical AQI reading for a specific ward.
    """
    timestamp: datetime = Field(..., description="Time of the reading")
    aqi: int = Field(..., description="Overall AQI value")
    category: str = Field(..., description="AQI Category")
    pm25: float = Field(..., description="PM2.5 concentration")
    pm10: float = Field(..., description="PM10 concentration")
    no2: float = Field(..., description="NO2 concentration")



# ---------------------------------------------------------------------------
# Person B — forecast + source attribution
# ---------------------------------------------------------------------------


class ForecastPoint(BaseModel):
    timestamp: str
    predicted_aqi: int
    trend: str               # rising | falling | stable
    lower: Optional[int] = None
    upper: Optional[int] = None


class FeatureImportance(BaseModel):
    feature: str
    importance: float
    description: str


class ForecastResponse(BaseModel):
    """GET /api/predict?ward_id=X&horizon=24|48|72 — 24/48/72h AQI forecast array."""
    ward_id: str
    horizon_hours: int       # 24 | 48 | 72
    points: list[ForecastPoint]
    model: str               # "LightGBM Regressor (Weather & Lag Tabular)"
    model_status: Optional[str] = "HEALTHY"
    warning: Optional[str] = None
    top_features: list[FeatureImportance] = []
    summary_reason: Optional[str] = None


class SourceBreakdown(BaseModel):
    """GET /api/source-attribution?ward=X — % breakdown by source + confidence + raw factors."""
    ward_id: str
    dominant_source: Optional[str] = None
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
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str] = []
