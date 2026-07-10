import asyncio
import os
import sys
import json

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.database import AsyncSessionLocal
from app.models.db_models import Ward
from sqlalchemy import func

async def add_dummy_ward():
    async with AsyncSessionLocal() as session:
        # Check if ward-1 exists
        ward_id = "ward-1"
        try:
            # Create a basic point geometry for Delhi (Connaught Place)
            point_geom = {
                "type": "Polygon",
                "coordinates": [[[77.21, 28.63], [77.22, 28.63], [77.22, 28.64], [77.21, 28.64], [77.21, 28.63]]]
            }
            new_ward = Ward(
                id=ward_id,
                name="Dummy Ward 1",
                area_sqkm=10.5,
                population=50000,
                geom=func.ST_SetSRID(func.ST_GeomFromGeoJSON(json.dumps(point_geom)), 4326)
            )
            session.add(new_ward)
            await session.commit()
            print("Successfully added dummy ward-1")
        except Exception as e:
            print(f"Error (might already exist): {e}")

if __name__ == "__main__":
    asyncio.run(add_dummy_ward())
