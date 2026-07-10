"""
AQI ingestion service for the ET AI Hackathon backend.
Responsible for fetching air quality data from OpenAQ and persisting it to the database.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from app.config import settings
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.db_models import AQIReading

# Target city coordinates for the hackathon
DEFAULT_CITY = "Delhi"
CITY_COORDS = {
    "Delhi": (28.6139, 77.2090)
}
OPEN_METEO_AQI_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


class AQIIngestionError(Exception):
    """Custom exception raised for errors during AQI ingestion."""
    pass


async def fetch_current_aqi(city: str = DEFAULT_CITY) -> Dict[str, Any]:
    """
    Fetches the latest current AQI and pollutant data for the target city from Open-Meteo.
    
    Args:
        city (str): Name of the target city.
        
    Returns:
        Dict[str, Any]: A dictionary containing current AQI data.
        
    Raises:
        AQIIngestionError: If the API request fails or the response is invalid.
    """
    coords = CITY_COORDS.get(city, CITY_COORDS[DEFAULT_CITY])
    
    params = {
        "latitude": coords[0],
        "longitude": coords[1],
        "current": "pm10,pm2_5,nitrogen_dioxide,us_aqi"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(OPEN_METEO_AQI_URL, params=params)
            response.raise_for_status()
            data = response.json()
            current_data = data.get("current", {})
            if not current_data:
                raise ValueError("No current data found for the specified location.")
            return current_data
        except httpx.RequestError as e:
            raise AQIIngestionError(f"Network error while fetching current AQI: {e}")
        except httpx.HTTPStatusError as e:
            raise AQIIngestionError(f"HTTP error while fetching current AQI: {e}")
        except ValueError as e:
            raise AQIIngestionError(f"Failed to parse JSON response or missing data: {e}")


async def fetch_historical_aqi(
    city: str = DEFAULT_CITY,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Historical AQI is skipped for now, but preserved for API signature compatibility.
    """
    pass


async def save_aqi_to_db(
    session: AsyncSession,
    ward_id: str,
    aqi_data: Dict[str, Any],
    timestamp: datetime
) -> AQIReading:
    """
    Saves an AQI reading to the database, avoiding duplicates.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        ward_id (str): The identifier of the ward.
        aqi_data (Dict[str, Any]): The AQI data dictionary.
        timestamp (datetime): The timestamp of the reading.
        
    Returns:
        AQIReading: The inserted or existing AQI reading database object.
        
    Raises:
        AQIIngestionError: If there is a database error.
    """
    try:
        stmt = select(AQIReading).where(
            AQIReading.ward_id == ward_id,
            AQIReading.timestamp == timestamp
        )
        result = await session.execute(stmt)
        existing_record = result.scalars().first()
        
        if existing_record:
            return existing_record
            
        # Parse Open-Meteo Air Quality current data
        # The structure is directly provided as key-value pairs
        pm25 = aqi_data.get("pm2_5")
        pm10 = aqi_data.get("pm10")
        no2 = aqi_data.get("nitrogen_dioxide")
        
        # Extract official AQI if available, otherwise default to 0.0
        official_aqi = aqi_data.get("us_aqi")
        aqi_value = float(official_aqi) if official_aqi is not None else 0.0
        
        dominant_pollutant = "unknown"
            
        new_reading = AQIReading(
            ward_id=ward_id,
            timestamp=timestamp,
            aqi_value=aqi_value,
            pm25=float(pm25) if pm25 is not None else None,
            pm10=float(pm10) if pm10 is not None else None,
            no2=float(no2) if no2 is not None else None,
            dominant_pollutant=dominant_pollutant
        )
        
        session.add(new_reading)
        await session.commit()
        await session.refresh(new_reading)
        
        return new_reading
    except SQLAlchemyError as e:
        await session.rollback()
        raise AQIIngestionError(f"Database error while saving AQI data: {e}")


async def get_latest_aqi(
    session: AsyncSession,
    ward_id: str
) -> Optional[AQIReading]:
    """
    Retrieves the most recent AQI reading for a specific ward.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        ward_id (str): The identifier of the ward.
        
    Returns:
        Optional[AQIReading]: The latest AQI reading object if found, else None.
        
    Raises:
        AQIIngestionError: If there is a database error.
    """
    try:
        stmt = (
            select(AQIReading)
            .where(AQIReading.ward_id == ward_id)
            .order_by(AQIReading.timestamp.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    except SQLAlchemyError as e:
        raise AQIIngestionError(f"Database error while retrieving latest AQI: {e}")


async def get_aqi(
    session: AsyncSession,
    ward_id: str,
    city: str = DEFAULT_CITY
) -> AQIReading:
    """
    High-level service function to orchestrate AQI ingestion.
    
    Fetches the latest current AQI from OpenAQ, saves it to the database,
    retrieves the most recently stored record for the ward, and returns it.
    This acts as the single entrypoint for routers to consume AQI data.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        ward_id (str): The identifier of the ward.
        city (str): Name of the target city.
        
    Returns:
        AQIReading: The latest AQI reading object from the database.
        
    Raises:
        AQIIngestionError: If the process fails at any step.
    """
    # 1. Fetch the latest AQI from OpenAQ
    aqi_data = await fetch_current_aqi(city)
    
    # 2. Use current UTC time as the timestamp since Open-Meteo gives realtime snapshots
    time_str = aqi_data.get("time")
    if time_str:
        try:
            timestamp = datetime.fromisoformat(time_str)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError, AttributeError):
            timestamp = datetime.now(timezone.utc)
    else:
        timestamp = datetime.now(timezone.utc)
    
    # 3. Save the reading into the database
    await save_aqi_to_db(session, ward_id, aqi_data, timestamp)
    
    # 4. Retrieve the stored record
    latest_aqi = await get_latest_aqi(session, ward_id)
    
    if not latest_aqi:
        raise AQIIngestionError("Failed to retrieve the latest AQI record after saving.")
        
    # 5. Return the latest AQIReading object
    return latest_aqi


async def get_aqi_history(
    session: AsyncSession,
    ward_id: str,
    days: int = 30
) -> List[AQIReading]:
    """
    Retrieves historical AQI records for a specific ward.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        ward_id (str): The identifier of the ward.
        days (int): Number of days of history to retrieve.
        
    Returns:
        List[AQIReading]: Historical AQI readings sorted by timestamp ascending.
        
    Raises:
        AQIIngestionError: If there is a database error.
    """
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(AQIReading)
            .where(AQIReading.ward_id == ward_id)
            .where(AQIReading.timestamp >= cutoff_date)
            .order_by(AQIReading.timestamp.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
    except SQLAlchemyError as e:
        raise AQIIngestionError(f"Database error while retrieving AQI history: {e}")
