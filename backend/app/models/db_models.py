from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.database import Base
from datetime import datetime, timezone

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

class Ward(Base):
    """
    Database model representing a city ward. Includes geospatial boundaries.
    """
    __tablename__ = "wards"

    id = Column(String, primary_key=True, index=True, comment="Unique identifier for the ward")
    name = Column(String, nullable=False, comment="Name of the ward")
    area_sqkm = Column(Float, nullable=False, comment="Area in square kilometers")
    population = Column(Integer, nullable=True, comment="Estimated population")
    geom = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False, comment="Geospatial boundaries of the ward")

    # Relationships
    aqi_readings = relationship("AQIReading", back_populates="ward", cascade="all, delete-orphan")
    weather_readings = relationship("WeatherReading", back_populates="ward", cascade="all, delete-orphan")
    traffic_readings = relationship("TrafficReading", back_populates="ward", cascade="all, delete-orphan")
    construction_readings = relationship("ConstructionReading", back_populates="ward", cascade="all, delete-orphan")


class AQIReading(Base):
    """
    Time-series model for Air Quality Index readings per ward.
    """
    __tablename__ = "aqi_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ward_id = Column(String, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    aqi_value = Column(Float, nullable=False, comment="Overall AQI value")
    pm25 = Column(Float, nullable=True, comment="PM2.5 concentration")
    pm10 = Column(Float, nullable=True, comment="PM10 concentration")
    no2 = Column(Float, nullable=True, comment="NO2 concentration")
    dominant_pollutant = Column(String, nullable=True, comment="Main pollutant driving the AQI")

    # Relationship
    ward = relationship("Ward", back_populates="aqi_readings")


class WeatherReading(Base):
    """
    Time-series model for weather conditions per ward.
    """
    __tablename__ = "weather_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ward_id = Column(String, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    temperature = Column(Float, nullable=False, comment="Temperature in Celsius")
    humidity = Column(Float, nullable=False, comment="Relative humidity percentage")
    wind_speed = Column(Float, nullable=False, comment="Wind speed in km/h")
    wind_direction = Column(Float, nullable=False, comment="Wind direction in degrees")
    precipitation = Column(Float, nullable=True, comment="Precipitation in mm")

    # Relationship
    ward = relationship("Ward", back_populates="weather_readings")


class TrafficReading(Base):
    """
    Time-series model for simulated traffic density per ward.
    """
    __tablename__ = "traffic_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ward_id = Column(String, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    traffic_index = Column(Float, nullable=False, comment="Simulated traffic density score")
    is_rush_hour = Column(Boolean, default=False, comment="Whether the reading was during rush hour")

    # Relationship
    ward = relationship("Ward", back_populates="traffic_readings")


class ConstructionReading(Base):
    """
    Time-series model for simulated construction activity per ward.
    """
    __tablename__ = "construction_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ward_id = Column(String, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    active_sites = Column(Integer, nullable=False, comment="Number of active construction sites")
    site_names = Column(JSON, nullable=False, default=list, comment="List of names of active construction sites")
    note = Column(String, nullable=True, comment="Additional context or notes about the construction")

    # Relationship
    ward = relationship("Ward", back_populates="construction_readings")


class IndustrialZone(Base):
    """
    Database model representing an industrial zone. Includes geospatial boundaries.
    """
    __tablename__ = "industrial_zones"

    id = Column(String, primary_key=True, index=True, comment="Unique identifier for the industrial zone")
    name = Column(String, nullable=False, comment="Name of the industrial zone")
    geom = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False, comment="Geospatial boundaries of the zone")


class RegulationChunk(Base):
    """
    RAG storage for Graded Response Action Plan (GRAP), CAQM directions,
    and statutory environmental acts.
    """
    __tablename__ = "regulation_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    doc_id = Column(String, index=True, nullable=False, comment="Document identifier e.g. 'GRAP-STAGE-III-01'")
    title = Column(String, nullable=False, comment="Title or formal heading")
    category = Column(String, index=True, nullable=False, comment="E.g. 'GRAP_STAGE_1', 'GRAP_STAGE_2', 'GRAP_STAGE_3', 'GRAP_STAGE_4', 'AIR_ACT_1981', 'CAQM_DIRECTION'")
    section = Column(String, nullable=True, comment="Specific Section or action item identifier")
    content = Column(Text, nullable=False, comment="Full text content of the regulatory chunk")
    legal_citation = Column(String, nullable=True, comment="Formal legal citation string")
    metadata_json = Column(JSON, nullable=True, comment="Additional metadata dict")
    embedding = Column(Vector(768) if Vector is not None else JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

