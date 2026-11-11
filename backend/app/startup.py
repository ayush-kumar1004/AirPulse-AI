"""Database bootstrap that runs automatically when the backend starts.

Without this, a fresh `docker compose up` gives you an empty Postgres and every
endpoint fails with `relation "wards" does not exist`. Previously the schema and
seed data only appeared if someone remembered to run scripts/init_db.py and
scripts/load_wards.py by hand.

Every step is idempotent, so restarting the stack is always safe.
"""
import logging

from sqlalchemy import func, select

from app.database import AsyncSessionLocal, Base, engine
from app.data_ingestion.aqi_refresh import refresh_all_ward_aqi
from app.data_ingestion.industrial import import_industrial_zones
from app.data_ingestion.wards import import_wards
from app.models import db_models  # noqa: F401 — registers every table on Base
from app.models.db_models import IndustrialZone, Ward

logger = logging.getLogger(__name__)


async def create_tables() -> None:
    """Create any missing tables. Existing tables and data are left alone."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ready.")


async def seed_wards() -> None:
    """Load the 290 Delhi wards from GeoJSON, but only into an empty table."""
    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(Ward))
        if count:
            logger.info("Wards already seeded (%s rows) — skipping.", count)
            return

        inserted = await import_wards(session)
        logger.info("Seeded %s wards.", inserted)


async def seed_industrial_zones() -> None:
    """Load industrial zones, but only into an empty table."""
    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(IndustrialZone))
        if count:
            logger.info("Industrial zones already seeded (%s rows) — skipping.", count)
            return

        inserted = await import_industrial_zones(session)
        logger.info("Seeded %s industrial zones.", inserted)


async def seed_aqi_readings() -> None:
    """Give every ward a current AQI reading so the heatmap has data to show.

    Without this the map renders flat: /api/heatmap reads `aqi_readings` and never
    populates it, so every ward reported aqi=0 / "Unknown".
    """
    async with AsyncSessionLocal() as session:
        count = await refresh_all_ward_aqi(session)
        logger.info("Initial AQI seeded for %s wards.", count)


async def ensure_forecasting_model() -> None:
    """Ensure the LightGBM forecasting model is trained and persisted."""
    from app.ml.forecast_model import GLOBAL_MODEL_PATH, train
    if not GLOBAL_MODEL_PATH.exists():
        logger.info("Forecasting model not found on startup — training LightGBM pipeline on historical data...")
        await train()
        logger.info("Forecasting model ready.")
    else:
        logger.info("Forecasting model already exists on disk — skipping training.")


async def ensure_regulatory_knowledge(sync_to_db: bool = True) -> None:
    """Ingest and verify statutory regulatory documents (GRAP, CAQM, Air Act) in the vector store."""
    from app.rag.vector_store import ingest_regulations
    count = await ingest_regulations(force_refresh=False, sync_to_db=sync_to_db)
    logger.info("Regulatory vector knowledge store ready (%s chunks).", count)


async def bootstrap_database() -> None:
    """Run the full bootstrap.

    Seeding failures are logged and swallowed on purpose: a missing GeoJSON file
    or offline database should not stop the API from booting. If PostgreSQL is offline,
    the system operates seamlessly in memory/cache/direct-API mode.
    """
    try:
        await create_tables()
    except Exception as e:
        logger.warning("Database schema initialization deferred (%s). Operating in direct-telemetry & cache mode.", e)
        # Skip DB-dependent table seeding steps when PostgreSQL is offline to ensure instant startup
        try:
            await ensure_forecasting_model()
            await ensure_regulatory_knowledge(sync_to_db=False)
        except Exception:
            logger.exception("Offline startup steps failed.")
        return

    for step in (
        seed_wards,
        seed_industrial_zones,
        seed_aqi_readings,
        ensure_forecasting_model,
        ensure_regulatory_knowledge,
    ):
        try:
            await step()
        except Exception:
            logger.exception("Seeding step %s failed — continuing startup.", step.__name__)
