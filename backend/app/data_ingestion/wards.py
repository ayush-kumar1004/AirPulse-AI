"""
Ward Loader service for the ET AI Hackathon backend.
Responsible for importing Delhi ward GeoJSON data into PostgreSQL/PostGIS.
"""

from typing import Dict, Any, List
import json
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from app.models.db_models import Ward

# Construct the default path dynamically based on this file's location
# Points to: backend/app/data/wards.geojson
DEFAULT_GEOJSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "data", 
    "wards.geojson"
)


class WardImportError(Exception):
    """Custom exception raised for errors during ward data ingestion."""
    pass


def load_geojson(filepath: str) -> Dict[str, Any]:
    """
    Loads and parses a GeoJSON file from disk.
    
    Args:
        filepath (str): The absolute or relative path to the GeoJSON file.
        
    Returns:
        Dict[str, Any]: The parsed JSON data as a dictionary.
        
    Raises:
        WardImportError: If the file is missing, unreadable, or contains invalid JSON.
    """
    if not os.path.exists(filepath):
        raise WardImportError(f"GeoJSON file not found at path: {filepath}")
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (IOError, ValueError) as e:
        raise WardImportError(f"Failed to read or parse GeoJSON file: {e}")


def parse_features(geojson_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validates the GeoJSON format and extracts the feature list.
    
    Args:
        geojson_data (Dict[str, Any]): The loaded GeoJSON dictionary.
        
    Returns:
        List[Dict[str, Any]]: A list of feature dictionaries.
        
    Raises:
        WardImportError: If the data is not a valid FeatureCollection.
    """
    if geojson_data.get("type") != "FeatureCollection":
        raise WardImportError("Invalid GeoJSON: Expected a FeatureCollection type.")
        
    features = geojson_data.get("features")
    if not isinstance(features, list):
        raise WardImportError("Invalid GeoJSON: 'features' key must contain a list.")
        
    return features


async def ward_exists(session: AsyncSession, ward_id: str) -> bool:
    """
    Checks if a ward already exists in the database.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        ward_id (str): The identifier of the ward.
        
    Returns:
        bool: True if the ward exists, False otherwise.
        
    Raises:
        WardImportError: If a database error occurs during the check.
    """
    try:
        stmt = select(Ward.id).where(Ward.id == ward_id)
        result = await session.execute(stmt)
        return result.scalars().first() is not None
    except SQLAlchemyError as e:
        raise WardImportError(f"Database error while checking existence of ward '{ward_id}': {e}")


async def save_wards_to_db(session: AsyncSession, features: List[Dict[str, Any]]) -> int:
    """
    Parses individual features and bulk-inserts them into the Ward table, skipping duplicates.
    Commits all changes in a single transaction.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        features (List[Dict[str, Any]]): The list of parsed GeoJSON features.
        
    Returns:
        int: The number of new wards successfully imported.
        
    Raises:
        WardImportError: If a database error occurs during insertion.
    """
    inserted_count = 0
    try:
        for feature in features:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry")
            
            # Extract standard properties with fallbacks for common GeoJSON schemas
            ward_id = properties.get("ward_id") or properties.get("id") or str(properties.get("OBJECTID", ""))
            ward_name = properties.get("ward_name") or properties.get("name") or properties.get("W_NAME", f"Unknown Ward {ward_id}")
            
            # The source GeoJSON carries one junk feature with ward_id "None" and every
            # name field null. Left in, it becomes an "Unknown Ward None" entry on the
            # map, so treat a literal "None" as missing.
            if not ward_id or str(ward_id) == "None" or not geometry:
                # Skip invalid features silently to continue processing
                continue

            ward_id_str = str(ward_id)
                
            # Check if the ward already exists to avoid duplicates
            if await ward_exists(session, ward_id_str):
                continue
                
            # Area calculation or fallback
            area_sqkm = float(properties.get("area_sqkm", 0.0))
            
            # Population parsing
            population = properties.get("population")
            if population is not None:
                population = int(population)
                
            # Create Ward instance with native PostGIS geometry parsing
            # We dump the raw geometry dict back to string and use ST_GeomFromGeoJSON
            new_ward = Ward(
                id=ward_id_str,
                name=str(ward_name),
                area_sqkm=area_sqkm,
                population=population,
                geom=func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(geometry)), 4326)
            )
            session.add(new_ward)
            inserted_count += 1
            
        # Commit once after iterating through all features
        await session.commit()
        return inserted_count
        
    except SQLAlchemyError as e:
        await session.rollback()
        raise WardImportError(f"Database error while saving wards: {e}")


async def import_wards(
    session: AsyncSession, 
    filepath: str = DEFAULT_GEOJSON_PATH
) -> int:
    """
    High-level orchestrator service to load Delhi ward GeoJSON data and import it into PostGIS.
    
    This function acts as the public entrypoint for initialization scripts and management commands.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        filepath (str, optional): Custom path to the GeoJSON file. Defaults to 'backend/app/data/wards.geojson'.
        
    Returns:
        int: The number of new wards successfully inserted.
        
    Raises:
        WardImportError: If any step of the import process fails.
    """
    # 1. Load GeoJSON from disk
    geojson_data = load_geojson(filepath)
    
    # 2. Validate format and extract features
    features = parse_features(geojson_data)
    
    # 3. Save to database (includes duplicate checks and single commit)
    inserted_count = await save_wards_to_db(session, features)
    
    return inserted_count


async def get_all_wards(session: AsyncSession) -> Dict[str, Any]:
    """
    Fetches all wards from the database and returns them as a GeoJSON FeatureCollection.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        
    Returns:
        Dict[str, Any]: A valid GeoJSON FeatureCollection.
        
    Raises:
        WardImportError: If a database error occurs.
    """
    try:
        stmt = select(Ward.id, Ward.name, func.ST_AsGeoJSON(Ward.geom).label('geojson'))
        result = await session.execute(stmt)
        
        features = []
        for row in result:
            feature = {
                "type": "Feature",
                "properties": {
                    "ward_id": row.id,
                    "ward_name": row.name
                },
                "geometry": json.loads(row.geojson)
            }
            features.append(feature)
            
        return {
            "type": "FeatureCollection",
            "features": features
        }
    except SQLAlchemyError as e:
        raise WardImportError(f"Database error while fetching wards: {e}")
