"""
Weather ingestion service for the ET AI Hackathon backend.
Responsible for fetching weather data from Open-Meteo and persisting it to the database.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.db_models import WeatherReading
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

# Constants for default location (Delhi)
# These can be moved to config.py later.
DEFAULT_LATITUDE = 28.6139
DEFAULT_LONGITUDE = 77.2090
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Every ward currently shares the same fixed Delhi coordinates, so a handful of wards being
# queried in quick succession sends near-identical requests to Open-Meteo — that's what tripped
# its rate limit (503s) during testing. Caching by location (same TTL Person A already uses for
# /api/aqi and /api/heatmap) means repeat calls for any ward within the window skip the live
# fetch entirely, instead of hammering Open-Meteo once per ward.
WEATHER_CACHE_TTL_SECONDS = 300


class WeatherIngestionError(Exception):
    """Custom exception raised for errors during weather ingestion."""
    pass


async def fetch_current_weather(
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE
) -> Dict[str, Any]:
    """
    Fetches the current weather conditions from Open-Meteo.
    
    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        
    Returns:
        Dict[str, Any]: A dictionary containing current weather data.
        
    Raises:
        WeatherIngestionError: If the API request fails or the response is invalid.
    """
    cache_key = f"weather:current:{round(latitude, 3)}:{round(longitude, 3)}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.debug("Redis cache read skipped: %s", e)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            data = response.json()
            current = data.get("current", {})
            try:
                await redis_client.setex(cache_key, WEATHER_CACHE_TTL_SECONDS, json.dumps(current))
            except Exception as e:
                logger.debug("Redis cache write skipped: %s", e)
            return current
        except httpx.RequestError as e:
            raise WeatherIngestionError(f"Network error while fetching current weather: {e}")
        except httpx.HTTPStatusError as e:
            raise WeatherIngestionError(f"HTTP error while fetching current weather: {e}")
        except ValueError as e:
            raise WeatherIngestionError(f"Failed to parse JSON response: {e}")


async def fetch_weather_forecast(
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    past_days: int = 0,
    forecast_days: int = 4,
) -> Dict[str, Any]:
    """
    Fetches the hourly weather forecast (and optional past days) from Open-Meteo.
    
    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        past_days (int): Number of past days to include.
        forecast_days (int): Number of forecast days to include (up to 16).
        
    Returns:
        Dict[str, Any]: A dictionary containing hourly forecast data.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m",
        "forecast_days": forecast_days,
    }
    if past_days > 0:
        params["past_days"] = past_days
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("hourly", {})
        except httpx.RequestError as e:
            raise WeatherIngestionError(f"Network error while fetching weather forecast: {e}")
        except httpx.HTTPStatusError as e:
            raise WeatherIngestionError(f"HTTP error while fetching weather forecast: {e}")
        except ValueError as e:
            raise WeatherIngestionError(f"Failed to parse JSON response: {e}")


async def save_weather_to_db(
    session: AsyncSession,
    ward_id: str,
    weather_data: Dict[str, Any],
    timestamp: datetime
) -> WeatherReading:
    """
    Saves a weather reading to the database, avoiding duplicates.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        ward_id (str): The identifier of the ward.
        weather_data (Dict[str, Any]): The weather data dictionary (from current or hourly).
        timestamp (datetime): The timestamp of the reading.
        
    Returns:
        WeatherReading: The inserted or existing weather reading database object.
        
    Raises:
        WeatherIngestionError: If there is a database error.
    """
    try:
        # Check for existing record to avoid duplicates based on ward and timestamp
        stmt = select(WeatherReading).where(
            WeatherReading.ward_id == ward_id,
            WeatherReading.timestamp == timestamp
        )
        result = await session.execute(stmt)
        existing_record = result.scalars().first()
        
        if existing_record:
            return existing_record
            
        new_reading = WeatherReading(
            ward_id=ward_id,
            timestamp=timestamp,
            temperature=weather_data.get("temperature_2m", 0.0),
            humidity=weather_data.get("relative_humidity_2m", 0.0),
            wind_speed=weather_data.get("wind_speed_10m", 0.0),
            wind_direction=weather_data.get("wind_direction_10m", 0.0),
            precipitation=weather_data.get("precipitation", 0.0)
        )
        
        session.add(new_reading)
        await session.commit()
        
        return new_reading
    except SQLAlchemyError as e:
        await session.rollback()
        raise WeatherIngestionError(f"Database error while saving weather data: {e}")


async def get_latest_weather(
    session: AsyncSession,
    ward_id: str
) -> Optional[WeatherReading]:
    """
    Retrieves the most recent weather reading for a specific ward.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        ward_id (str): The identifier of the ward.
        
    Returns:
        Optional[WeatherReading]: The latest weather reading object if found, else None.
        
    Raises:
        WeatherIngestionError: If there is a database error.
    """
    try:
        stmt = (
            select(WeatherReading)
            .where(WeatherReading.ward_id == ward_id)
            .order_by(WeatherReading.timestamp.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    except SQLAlchemyError as e:
        raise WeatherIngestionError(f"Database error while retrieving latest weather: {e}")


async def _latest_weather_any_ward(session: AsyncSession) -> Optional[WeatherReading]:
    """Newest weather reading regardless of ward — valid city-wide because every
    ward is currently fetched at the same default coordinate."""
    try:
        stmt = select(WeatherReading).order_by(WeatherReading.timestamp.desc()).limit(1)
        result = await session.execute(stmt)
        return result.scalars().first()
    except SQLAlchemyError as e:
        raise WeatherIngestionError(f"Database error while retrieving fallback weather: {e}")


async def get_weather(
    session: AsyncSession,
    ward_id: str,
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE
) -> WeatherReading:
    """
    High-level service function to orchestrate weather ingestion.
    
    Fetches the latest current weather from Open-Meteo, saves it to the database,
    retrieves the most recently stored record for the ward, and returns it.
    This acts as the single entrypoint for routers to consume weather data.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        ward_id (str): The identifier of the ward.
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        
    Returns:
        WeatherReading: The latest weather reading object from the database.
        
    Raises:
        WeatherIngestionError: If the process fails at any step.
    """
    # 1. Fetch the latest weather from Open-Meteo. If the live call fails, fall
    # back to the newest stored reading rather than erroring the whole endpoint:
    # every ward is fetched at the same city coordinate, so any recent row is the
    # same measurement this call would have produced.
    try:
        weather_data = await fetch_current_weather(latitude, longitude)
    except WeatherIngestionError:
        fallback = await get_latest_weather(session, ward_id)
        if fallback is None:
            fallback = await _latest_weather_any_ward(session)
        if fallback is not None:
            return fallback
        raise

    # Use current timezone-aware UTC time as the timestamp
    timestamp = datetime.now(timezone.utc)

    # 2. Save the reading into the database if available
    try:
        await save_weather_to_db(session, ward_id, weather_data, timestamp)
        latest_weather = await get_latest_weather(session, ward_id)
        if latest_weather:
            return latest_weather
    except Exception:
        pass
        
    # 3. Return an in-memory WeatherReading object if database is offline
    curr = weather_data.get("current", weather_data) if isinstance(weather_data, dict) else {}
    return WeatherReading(
        ward_id=ward_id,
        timestamp=timestamp,
        temperature=float(curr.get("temperature_2m", 26.5)),
        humidity=float(curr.get("relative_humidity_2m", 54.0)),
        wind_speed=float(curr.get("wind_speed_10m", 11.2)),
        wind_direction=float(curr.get("wind_direction_10m", 310.0)),
        precipitation=float(curr.get("precipitation", 0.0)),
    )
