# TODO: Person A — Postgres + PostGIS connection (SQLAlchemy engine, session, Base, get_db()).
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

# TODO: Person A — tune pool settings; ensure PostGIS extension is created on startup
#   (run: CREATE EXTENSION IF NOT EXISTS postgis;)
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
