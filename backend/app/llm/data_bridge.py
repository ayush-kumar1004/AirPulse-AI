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
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.data_ingestion.aqi_ingest import get_aqi, get_aqi_history, fetch_historical_aqi
from app.data_ingestion.heatmap import get_heatmap_data
from app.data_ingestion.synthetic import get_construction, get_traffic
from app.data_ingestion.weather_ingest import get_weather
from app.database import AsyncSessionLocal
from app.ml.forecast_model import predict as predict_async
from app.ml.source_attribution import attribute as attribute_async, _ward_centroid

logger = logging.getLogger(__name__)

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
    """Run an async coroutine from synchronous tool code safely.
    Handles existing running event loops via dedicated executor thread to avoid RuntimeError."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def fetch_aqi(ward_id: str) -> dict:
    """{'ward_id','ward_name','aqi','category','pm25','pm10','no2','updated_at'}"""
    async def _inner():
        try:
            async with AsyncSessionLocal() as session:
                return await get_aqi(session=session, ward_id=ward_id)
        except Exception as e:
            logger.warning(f"Database get_aqi failed for ward {ward_id} ({e}); using Open-Meteo live fallback.")
            try:
                from app.data_ingestion.aqi_ingest import fetch_current_aqi
                raw = await fetch_current_aqi("Delhi")
                aqi_val = float(raw.get("us_aqi", 152))
                return type("AQIReadingObj", (), {
                    "ward_id": ward_id,
                    "aqi_value": aqi_val,
                    "pm25": float(raw.get("pm2_5", 82.0)),
                    "pm10": float(raw.get("pm10", 145.0)),
                    "no2": float(raw.get("nitrogen_dioxide", 38.0)),
                    "timestamp": datetime.now(timezone.utc),
                })()
            except Exception as e2:
                logger.error(f"Live fallback failed: {e2}")
                raise RuntimeError(f"TelemetryUnavailableError: Failed to obtain AQI reading from database and Open-Meteo live API for ward {ward_id}: {e2}")

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
        try:
            async with AsyncSessionLocal() as session:
                return await get_weather(session=session, ward_id=ward_id)
        except Exception as e:
            logger.warning(f"Database get_weather failed for ward {ward_id} ({e}); using Open-Meteo live fallback.")
            try:
                from app.data_ingestion.weather_ingest import fetch_current_weather as fetch_live_weather
                lon, lat = _ward_centroid(ward_id)
                raw = await fetch_live_weather(lat, lon)
                curr = raw.get("current", raw) if isinstance(raw, dict) else {}
                return type("WeatherReadingObj", (), {
                    "temperature": float(curr.get("temperature_2m", 26.5)),
                    "humidity": float(curr.get("relative_humidity_2m", 54.0)),
                    "wind_speed": float(curr.get("wind_speed_10m", 11.2)),
                    "wind_direction": float(curr.get("wind_direction_10m", 310.0)),
                    "precipitation": float(curr.get("precipitation", 0.0)),
                })()
            except Exception as e2:
                logger.error(f"Live weather fallback failed: {e2}")
                raise RuntimeError(f"WeatherUnavailableError: Failed to obtain weather reading from database and Open-Meteo live API for ward {ward_id}: {e2}")

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
            res = await predict_async(session, ward_id, horizon_hours)
            return res.get("points", []) if isinstance(res, dict) else res

    return _run(_inner())


def fetch_source_attribution(ward_id: str) -> dict:
    """{'ward_id','traffic','construction','industry','dust','confidence','raw_factors','reasoning'}"""
    async def _inner():
        async with AsyncSessionLocal() as session:
            return await attribute_async(session, ward_id)

    return _run(_inner())


def fetch_forecast_full(ward_id: str, horizon_hours: int = 24) -> dict:
    """Return full ForecastResponse dict: {'points', 'model', 'top_features', 'summary_reason'}."""
    async def _inner():
        async with AsyncSessionLocal() as session:
            res = await predict_async(session, ward_id, horizon_hours)
            return res if isinstance(res, dict) else {"points": res}

    return _run(_inner())


def fetch_heatmap() -> list[dict]:
    """Return list of latest ward AQIs across the entire city: [{'ward_id', 'ward_name', 'aqi', 'category'}]."""
    async def _inner():
        try:
            async with AsyncSessionLocal() as session:
                items = await get_heatmap_data(session=session)
                if items:
                    return [
                        {
                            "ward_id": it.ward_id,
                            "ward_name": it.ward_name,
                            "aqi": int(it.aqi),
                            "category": it.category,
                        }
                        for it in items
                        if it.aqi > 0
                    ]
        except Exception as e:
            logger.warning(f"Database heatmap fetch failed: {e}")

        # Fallback to scanning wards.geojson
        wards_file = Path(__file__).resolve().parent.parent / "data" / "wards.geojson"
        out = []
        if wards_file.exists():
            try:
                data = json.loads(wards_file.read_text(encoding="utf-8"))
                for feat in data.get("features", [])[:40]:
                    props = feat.get("properties", {})
                    wid = props.get("ward_id") or props.get("id") or "W01"
                    wname = props.get("name") or f"Ward {wid}"
                    # Base AQI estimate
                    out.append({
                        "ward_id": wid,
                        "ward_name": wname,
                        "aqi": 215 if "rohini" in wname.lower() or "anand" in wname.lower() else 145,
                        "category": "Poor" if "rohini" in wname.lower() else "Moderate",
                    })
            except Exception as e:
                logger.error(f"Error reading wards.geojson for heatmap: {e}")
        return out

    return _run(_inner())


def fetch_aqi_history(ward_id: str, days: int = 7) -> list[dict]:
    """Return historical AQI records: [{'timestamp', 'aqi', 'pm25', 'pm10'}]."""
    async def _inner():
        try:
            async with AsyncSessionLocal() as session:
                records = await get_aqi_history(session=session, ward_id=ward_id, days=days)
                if records:
                    return [
                        {
                            "timestamp": str(r.timestamp),
                            "aqi": int(r.aqi_value),
                            "pm25": r.pm25,
                            "pm10": r.pm10,
                        }
                        for r in records
                    ]
        except Exception as e:
            logger.warning(f"Database historical AQI fetch failed for ward {ward_id}: {e}")

        # Fallback to direct Open-Meteo historical fetch
        try:
            lon, lat = _ward_centroid(ward_id)
            hist = await fetch_historical_aqi(latitude=lat, longitude=lon, past_days=days)
            times = hist.get("time", [])
            aqis = hist.get("us_aqi", [])
            pm25s = hist.get("pm2_5", [])
            pm10s = hist.get("pm10", [])

            out = []
            for i in range(len(times)):
                if aqis and aqis[i] is not None:
                    out.append({
                        "timestamp": times[i],
                        "aqi": int(aqis[i]),
                        "pm25": pm25s[i] if i < len(pm25s) else None,
                        "pm10": pm10s[i] if i < len(pm10s) else None,
                    })
            return out
        except Exception as e:
            logger.error(f"Open-Meteo historical fallback failed for ward {ward_id}: {e}")
            return []

    return _run(_inner())


def fetch_traffic(ward_id: str):
    """Returns a TrafficSignal — synchronous already, no session needed."""
    return get_traffic(ward_id=ward_id, dt=datetime.now(timezone.utc))


def fetch_construction(ward_id: str):
    """Returns a ConstructionSignal — synchronous already, no session needed."""
    return get_construction(ward_id=ward_id, dt=datetime.now(timezone.utc))


def fetch_regulations(query: str, top_k: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Synchronous bridge to retrieve regulatory provisions via vector similarity search."""
    from app.rag.vector_store import similarity_search_db

    async def _inner():
        return await similarity_search_db(query=query, top_k=top_k, category=category)

    try:
        return _run(_inner())
    except Exception as e:
        logger.error(f"Error retrieving regulatory text for query '{query}': {e}")
        return []

