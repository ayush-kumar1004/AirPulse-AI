import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure the backend directory is in the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from app.database import AsyncSessionLocal
from app.data_ingestion.industrial import import_industrial_zones, IndustrialImportError

async def main():
    print("Starting industrial zone import process...")
    try:
        async with AsyncSessionLocal() as session:
            inserted = await import_industrial_zones(session)
            print(f"Import succeeded! Inserted {inserted} industrial zones.")
    except IndustrialImportError as e:
        print(f"Import failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
