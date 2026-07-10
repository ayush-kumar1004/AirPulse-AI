from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.db_models import Ward, AQIReading
from app.models.schemas import HeatmapWard

class HeatmapError(Exception):
    """Custom exception raised for errors during heatmap data retrieval."""
    pass

async def get_heatmap_data(session: AsyncSession) -> List[HeatmapWard]:
    """
    Fetches the latest AQI reading for every ward to power the pollution heatmap.
    Uses PostgreSQL DISTINCT ON to efficiently get the most recent reading per ward.
    
    Args:
        session (AsyncSession): The SQLAlchemy async session.
        
    Returns:
        List[HeatmapWard]: A list of wards with their current AQI values and categories.
        
    Raises:
        HeatmapError: If a database error occurs.
    """
    try:
        # Use DISTINCT ON to get only the most recent AQI reading for each ward
        # Use outerjoin to ensure ALL wards are returned even if they lack an AQI reading
        stmt = (
            select(Ward.id, Ward.name, AQIReading.aqi_value)
            .outerjoin(AQIReading, Ward.id == AQIReading.ward_id)
            .distinct(Ward.id)
            .order_by(Ward.id, AQIReading.timestamp.desc().nulls_last())
        )
        result = await session.execute(stmt)
        
        heatmap_data = []
        for row in result:
            ward_id = row.id
            ward_name = row.name
            aqi_val = row.aqi_value
            
            # Simple AQI categorization logic with fallback for missing readings
            if aqi_val is None:
                aqi_val = 0
                category = "Unknown"
            elif aqi_val <= 50:
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
                
            heatmap_data.append(
                HeatmapWard(
                    ward_id=ward_id,
                    ward_name=ward_name,
                    aqi=int(aqi_val),
                    category=category
                )
            )
            
        return heatmap_data
    except SQLAlchemyError as e:
        raise HeatmapError(f"Database error while fetching heatmap data: {e}")
