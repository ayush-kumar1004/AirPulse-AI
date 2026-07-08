# TODO: Person A — SQLAlchemy ORM tables (wards w/ PostGIS geometry, aqi_readings, weather, synthetic_signals).
# Example skeleton below — flesh out columns, indexes, and the PostGIS geometry column.
from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database import Base


class Ward(Base):
    __tablename__ = "wards"
    # TODO: Person A — add geom = Column(Geometry("POLYGON", srid=4326)) via GeoAlchemy2
    id = Column(String, primary_key=True)          # ward_id
    name = Column(String, nullable=False)


class AQIReading(Base):
    __tablename__ = "aqi_readings"
    # TODO: Person A — real ingestion writes here (OpenAQ/CPCB)
    id = Column(Integer, primary_key=True, autoincrement=True)
    ward_id = Column(String, index=True)
    aqi = Column(Integer)
    pm25 = Column(Float)
    pm10 = Column(Float)
    recorded_at = Column(DateTime, index=True)
