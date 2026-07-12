"""Person C — sync bridge to the real (async) data + ML layers.

Why this exists: Mukul's agents (recommendation_agent.py, citizen_advisor.py, tools.py) are plain
synchronous functions, called from a synchronous FastAPI route (routers/agents.py) — LangGraph's
create_react_agent works most simply with sync @tool functions. But Person A's real data functions
(app.data_ingestion.*) and Person B's ML functions (app.ml.*) are async and need a DB session. This
module opens a short-lived session and runs the async call to completion, so every other file in
app/llm/ can just call a plain function and get a plain dict back.

If a future pass moves the agent layer to async end-to-end, these wrappers can go away and callers
can `await` the underlying functions directly instead.
"""
import asyncio
from datetime import datetime, timezone

from app.data_ingestion.aqi_ingest import get_aqi
from app.data_ingestion.synthetic import get_construction, get_traffic
from app.data_ingestion.weather_ingest import get_weather
from app.database import AsyncSessionLocal
from app.ml.forecast_model import predict as predict_async
from app.ml.source_attribution import attribute as attribute_async

COMPASS_LABELS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def _compass_label(degrees: float) -> str:
    return COMPASS_LABELS[round(degrees / 45) % 8]


def _categorize(aqi_value: float) -> str:
    """Matches the categorisation in routers/data.py exactly, so agents describe AQI the same
    way the rest of the app does."""
    if aqi_value <= 50:
        return "Good"
    elif aqi_value <= 100:
        return "Satisfactory"
    elif aqi_value <= 200:
        return "Moderate"
    elif aqi_value <= 300:
        return "Poor"
    elif aqi_value <= 400:
        return "Very Poor"
    return "Severe"


def _run(coro):
    return asyncio.run(coro)


def fetch_aqi(ward_id: str) -> dict:
    """{'ward_id','ward_name','aqi','category','pm25','pm10','no2','updated_at'}"""
    async def _inner():
        async with AsyncSessionLocal() as session:
            return await get_aqi(session=session, ward_id=ward_id)

    reading = _run(_inner())
    return {
        "ward_id": reading.ward_id,
        "ward_name": f"Ward {reading.ward_id}",
        "aqi": int(reading.aqi_value),
        "category": _categorize(reading.aqi_value),
        "pm25": reading.pm25 or 0.0,
        "pm10": reading.pm10 or 0.0,
        "no2": reading.no2 or 0.0,
        "updated_at": reading.timestamp,
    }


def fetch_weather(ward_id: str) -> dict:
    """{'temp_c','humidity','wind_kph','wind_dir','wind_deg','rain_mm'}"""
    async def _inner():
        async with AsyncSessionLocal() as session:
            return await get_weather(session=session, ward_id=ward_id)

    reading = _run(_inner())
    return {
        "temp_c": reading.temperature,
        "humidity": reading.humidity,
        "wind_kph": reading.wind_speed,
        "wind_dir": _compass_label(reading.wind_direction),
        "wind_deg": reading.wind_direction,
        "rain_mm": reading.precipitation,
    }


def fetch_forecast(ward_id: str, horizon_hours: int = 24) -> list[dict]:
    """[{'timestamp','predicted_aqi','trend','lower','upper'}, ...]"""
    async def _inner():
        async with AsyncSessionLocal() as session:
            return await predict_async(session, ward_id, horizon_hours)

    return _run(_inner())


def fetch_source_attribution(ward_id: str) -> dict:
    """{'ward_id','traffic','construction','industry','dust','confidence','raw_factors','reasoning'}"""
    async def _inner():
        async with AsyncSessionLocal() as session:
            return await attribute_async(session, ward_id)

    return _run(_inner())


def fetch_traffic(ward_id: str):
    """Returns a TrafficSignal — synchronous already, no session needed."""
    return get_traffic(ward_id=ward_id, dt=datetime.now(timezone.utc))


def fetch_construction(ward_id: str):
    """Returns a ConstructionSignal — synchronous already, no session needed."""
    return get_construction(ward_id=ward_id, dt=datetime.now(timezone.utc))
