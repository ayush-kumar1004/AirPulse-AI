import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure the backend directory is in the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from app.database import AsyncSessionLocal
from app.data_ingestion.wards import import_wards, WardImportError

async def load_wards():
    print("Starting ward import process...")
    async with AsyncSessionLocal() as session:
        try:
            # We assume the geojson is at app/data/wards.geojson
            filepath = os.path.join(backend_dir, "app", "data", "wards.geojson")
            inserted_count = await import_wards(session, filepath=filepath)
            print(f"Import succeeded! Inserted {inserted_count} wards.")
        except WardImportError as e:
            print(f"Failed to import wards: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(load_wards())
