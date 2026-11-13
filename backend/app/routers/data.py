"""
Data router for the ET AI Hackathon backend.
Exposes endpoints to fetch weather, AQI, traffic, and construction data.
Strictly delegates all business logic and data fetching to the service layer.
"""

from typing import Optional, Any, List, Tuple
from datetime import datetime, timezone
import time
import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import Ward
from app.models.schemas import TrafficSignal, ConstructionSignal, WeatherResponse, WardAQI, HeatmapWard, AQIHistoryRecord
from app.redis_client import redis_client

# Service functions
from app.data_ingestion.weather_ingest import get_weather, WeatherIngestionError
from app.data_ingestion.aqi_ingest import get_aqi, get_aqi_history, AQIIngestionError
from app.data_ingestion.synthetic import get_traffic, get_construction
from app.data_ingestion.wards import get_all_wards, WardImportError
from app.data_ingestion.heatmap import get_heatmap_data, HeatmapError


router = APIRouter()

_IN_MEM_HEATMAP_CACHE: Optional[Tuple[float, Any]] = None
_IN_MEM_AQI_CACHE: dict[str, Tuple[float, Any]] = {}


@router.get("/wards")
async def get_wards_endpoint(session: AsyncSession = Depends(get_db)) -> Any:
    """
    Fetches all ward polygons from the PostGIS database.
    Returns a valid GeoJSON FeatureCollection.
    """
    try:
        return await get_all_wards(session=session)
    except WardImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An unexpected error occurred while fetching wards."
        )


@router.get("/heatmap", response_model=List[HeatmapWard])
async def get_heatmap_endpoint(session: AsyncSession = Depends(get_db)) -> Any:
    """
    Fetches AQI information for ALL wards to render the pollution heatmap.
    Returns exactly one object per ward with the latest AQI reading.
    """
    global _IN_MEM_HEATMAP_CACHE
    now = time.time()
    if _IN_MEM_HEATMAP_CACHE and (now - _IN_MEM_HEATMAP_CACHE[0]) < 300:
        return _IN_MEM_HEATMAP_CACHE[1]

    cache_key = "heatmap"
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            parsed = json.loads(cached_data)
            _IN_MEM_HEATMAP_CACHE = (now, parsed)
            return parsed
    except Exception:
        pass

    try:
        data = await get_heatmap_data(session=session)
        try:
            dumped = [w.model_dump(mode='json') for w in data]
            await redis_client.setex(cache_key, 300, json.dumps(dumped))
        except Exception:
            pass
        _IN_MEM_HEATMAP_CACHE = (now, data)
        return data
    except HeatmapError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An unexpected error occurred while fetching heatmap data."
        )


@router.get("/weather")
async def get_weather_endpoint(
    ward_id: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    session: AsyncSession = Depends(get_db)
) -> Any:
    """
    Fetches the latest weather reading for a specific ward.
    Delegates entirely to the get_weather service function.
    """
    try:
        # Build kwargs to only pass coordinates if they were explicitly provided
        kwargs = {}
        if latitude is not None:
            kwargs["latitude"] = latitude
        if longitude is not None:
            kwargs["longitude"] = longitude
            
        reading = await get_weather(session=session, ward_id=ward_id, **kwargs)
        return WeatherResponse(
            ward_id=reading.ward_id,
            timestamp=reading.timestamp,
            temperature=reading.temperature,
            humidity=reading.humidity,
            wind_speed=reading.wind_speed,
            wind_direction=reading.wind_direction,
            precipitation=reading.precipitation
        )
    except WeatherIngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, 
            detail=f"Weather service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An unexpected error occurred while fetching weather data."
        )


@router.get("/aqi")
async def get_aqi_endpoint(
    ward_id: str,
    city: str = "Delhi",
    session: AsyncSession = Depends(get_db)
) -> Any:
    """
    Fetches the latest AQI reading for a specific ward.
    Delegates entirely to the get_aqi service function.
    """
    global _IN_MEM_AQI_CACHE
    now = time.time()
    if ward_id in _IN_MEM_AQI_CACHE and (now - _IN_MEM_AQI_CACHE[ward_id][0]) < 300:
        return _IN_MEM_AQI_CACHE[ward_id][1]

    cache_key = f"aqi:{ward_id}"
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            parsed = json.loads(cached_data)
            _IN_MEM_AQI_CACHE[ward_id] = (now, parsed)
            return parsed
    except Exception:
        pass

    try:
        reading = await get_aqi(session=session, ward_id=ward_id, city=city)

        # Resolve the real ward name so the UI shows "ROHINI", not "Ward 21".
        ward_name = None
        try:
            ward_name = await session.scalar(select(Ward.name).where(Ward.id == ward_id))
        except Exception:
            pass
        if not ward_name:
            from app.data_ingestion.cpcb_aqi import get_ward_info
            ward_name = get_ward_info(ward_id).get("ward_name")

        # Simple AQI categorization logic for the hackathon
        aqi_val = reading.aqi_value
        if aqi_val <= 50:
            category = "Good"
        elif aqi_val <= 100:
            category = "Satisfactory"
        elif aqi_val <= 200:
            category = "Moderate"
        elif aqi_val <= 300:
            category = "Poor"
        elif aqi_val <= 400:
            category = "Very Poor"
        else:
            category = "Severe"
            
        response_data = WardAQI(
            ward_id=reading.ward_id,
            ward_name=ward_name or f"Ward {reading.ward_id}",
            aqi=int(aqi_val),
            category=category,
            pm25=reading.pm25 or 0.0,
            pm10=reading.pm10 or 0.0,
            no2=reading.no2 or 0.0,
            updated_at=reading.timestamp
        )
        
        try:
            await redis_client.setex(cache_key, 300, json.dumps(response_data.model_dump(mode='json')))
        except Exception:
            pass
        _IN_MEM_AQI_CACHE[ward_id] = (now, response_data)
        return response_data
    except AQIIngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, 
            detail=f"AQI service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An unexpected error occurred while fetching AQI data."
        )


@router.get("/aqi/history", response_model=List[AQIHistoryRecord])
async def get_aqi_history_endpoint(
    ward_id: str = Query(..., description="The identifier of the ward"),
    days: int = Query(30, description="Number of days of history to retrieve"),
    session: AsyncSession = Depends(get_db)
) -> List[AQIHistoryRecord]:
    """
    Fetches the historical AQI records for a specific ward.
    """
    try:
        readings = await get_aqi_history(session=session, ward_id=ward_id, days=days)
        
        history = []
        for reading in readings:
            aqi_val = reading.aqi_value
            if aqi_val <= 50:
                category = "Good"
            elif aqi_val <= 100:
                category = "Satisfactory"
            elif aqi_val <= 200:
                category = "Moderate"
            elif aqi_val <= 300:
                category = "Poor"
            elif aqi_val <= 400:
                category = "Very Poor"
            else:
                category = "Severe"
                
            history.append(
                AQIHistoryRecord(
                    timestamp=reading.timestamp,
                    aqi=int(aqi_val),
                    category=category,
                    pm25=reading.pm25 or 0.0,
                    pm10=reading.pm10 or 0.0,
                    no2=reading.no2 or 0.0
                )
            )
            
        return history
    except AQIIngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AQI service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An unexpected error occurred while fetching historical AQI data."
        )


@router.get("/traffic", response_model=TrafficSignal)
async def get_traffic_endpoint(
    ward_id: str,
    target_datetime: Optional[datetime] = Query(None, alias="datetime")
) -> TrafficSignal:
    """
    Generates a deterministic synthetic traffic signal for a specific ward.
    Delegates entirely to the get_traffic synthetic service function.
    """
    # Use provided datetime or fallback to current UTC time
    dt = target_datetime or datetime.now(timezone.utc)
    
    try:
        return get_traffic(ward_id=ward_id, dt=dt)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error generating traffic signal: {str(e)}"
        )


@router.get("/construction", response_model=ConstructionSignal)
async def get_construction_endpoint(
    ward_id: str,
    target_datetime: Optional[datetime] = Query(None, alias="datetime")
) -> ConstructionSignal:
    """
    Generates a deterministic synthetic construction signal for a specific ward.
    Delegates entirely to the get_construction synthetic service function.
    """
    dt = target_datetime or datetime.now(timezone.utc)
    
    try:
        return get_construction(ward_id=ward_id, dt=dt)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error generating construction signal: {str(e)}"
        )
