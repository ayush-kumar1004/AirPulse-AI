"""
Industrial Zones Loader service for the ET AI Hackathon backend.
Responsible for importing Delhi industrial zones GeoJSON data into PostgreSQL/PostGIS.
"""

from typing import Dict, Any, List
import json
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from app.models.db_models import IndustrialZone

DEFAULT_GEOJSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "data", 
    "industrial_zones.geojson"
)


class IndustrialImportError(Exception):
    """Custom exception raised for errors during industrial zone ingestion."""
    pass


def load_geojson(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        raise IndustrialImportError(f"GeoJSON file not found at path: {filepath}")
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (IOError, ValueError) as e:
        raise IndustrialImportError(f"Failed to read or parse GeoJSON file: {e}")


def parse_features(geojson_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    if geojson_data.get("type") != "FeatureCollection":
        raise IndustrialImportError("Invalid GeoJSON: Expected a FeatureCollection type.")
        
    features = geojson_data.get("features")
    if not isinstance(features, list):
        raise IndustrialImportError("Invalid GeoJSON: 'features' key must contain a list.")
        
    return features


async def zone_exists(session: AsyncSession, zone_id: str) -> bool:
    try:
        stmt = select(IndustrialZone.id).where(IndustrialZone.id == zone_id)
        result = await session.execute(stmt)
        return result.scalars().first() is not None
    except SQLAlchemyError as e:
        raise IndustrialImportError(f"Database error while checking existence of zone '{zone_id}': {e}")


async def save_zones_to_db(session: AsyncSession, features: List[Dict[str, Any]]) -> int:
    inserted_count = 0
    try:
        for feature in features:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry")
            
            zone_id = properties.get("id") or properties.get("OBJECTID")
            zone_name = properties.get("name") or properties.get("NAME") or f"Zone {zone_id}"
            
            if not zone_id or not geometry:
                continue
                
            zone_id_str = str(zone_id)
                
            if await zone_exists(session, zone_id_str):
                continue
                
            new_zone = IndustrialZone(
                id=zone_id_str,
                name=str(zone_name),
                geom=func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(geometry)), 4326)
            )
            session.add(new_zone)
            inserted_count += 1
            
        await session.commit()
        return inserted_count
        
    except SQLAlchemyError as e:
        await session.rollback()
        raise IndustrialImportError(f"Database error while saving zones: {e}")


async def import_industrial_zones(
    session: AsyncSession, 
    filepath: str = DEFAULT_GEOJSON_PATH
) -> int:
    """
    High-level orchestrator service to load Delhi industrial zones GeoJSON data and import it into PostGIS.
    """
    geojson_data = load_geojson(filepath)
    features = parse_features(geojson_data)
    inserted_count = await save_zones_to_db(session, features)
    
    return inserted_count
