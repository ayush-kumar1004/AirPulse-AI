import asyncio
import os
import sys

# Ensure the backend directory is in the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.database import engine, Base
# Import db_models to ensure Base knows about all models
from app.models import db_models

async def init_db():
    print("Initializing database schema...")
    try:
        async with engine.begin() as conn:
            # We use run_sync to execute the synchronous create_all in an async context
            await conn.run_sync(Base.metadata.create_all)
        print("Database schema initialization complete!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise e
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
