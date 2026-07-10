# TODO: Person A — Data & Backend router. Owns DOCX Section 6 endpoints:
#   /api/wards  /api/aqi  /api/weather  /api/heatmap  /api/traffic  /api/construction
# Returns MOCK data now; swap internals for app.data_ingestion.* + DB queries. No mock data left by Day 9.
from fastapi import APIRouter, Query

from app.models.schemas import ConstructionSignal, HeatmapWard, TrafficSignal, WardAQI

router = APIRouter(prefix="/api", tags=["data (Person A)"])


@router.get("/wards")
def list_wards():
    """List of ward GeoJSON polygons + metadata. TODO: Person A — app.data_ingestion.wards."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"ward_id": "W01", "ward_name": "Connaught Place"},
                "geometry": {"type": "Polygon", "coordinates": [[[77.21, 28.63], [77.23, 28.63], [77.23, 28.645], [77.21, 28.645], [77.21, 28.63]]]},
            }
        ],
    }


@router.get("/aqi", response_model=WardAQI)
def current_aqi(ward: str = Query(..., description="ward_id")):
    """Current AQI + pollutant breakdown for a ward. TODO: Person A — query aqi_readings + Redis cache."""
    return WardAQI(ward_id=ward, ward_name="Connaught Place", aqi=182, category="poor",
                   pm25=98.0, pm10=210.0, no2=44.0, updated_at="2026-07-06T09:00:00Z")


@router.get("/weather")
def weather(ward: str = Query(..., description="ward_id")):
    """Current + forecast weather for a ward. TODO: Person A — app.data_ingestion.weather_ingest (Open-Meteo)."""
    return {"ward_id": ward, "temp_c": 34.2, "humidity": 41, "wind_kph": 8.0, "wind_dir": "NW", "rain_mm": 0.0}


@router.get("/heatmap", response_model=list[HeatmapWard])
def heatmap():
    """Per-ward AQI snapshot for map colouring (ALL wards). TODO: Person A — cache heavily in Redis."""
    return [
        HeatmapWard(ward_id="W01", ward_name="Connaught Place", aqi=182, category="poor"),
        HeatmapWard(ward_id="W02", ward_name="Rohini", aqi=241, category="severe"),
    ]


@router.get("/traffic", response_model=TrafficSignal)
def traffic(ward: str = Query(..., description="ward_id")):
    """SIMULATED traffic density score. TODO: Person A — app.data_ingestion.synthetic (rush-hour weighted)."""
    return TrafficSignal(ward_id=ward, traffic_index=0.72)


@router.get("/construction", response_model=ConstructionSignal)
def construction(ward: str = Query(..., description="ward_id")):
    """SIMULATED active construction sites. TODO: Person A — app.data_ingestion.synthetic."""
    return ConstructionSignal(ward_id=ward, active_sites=2, site_names=["Metro Phase-4 site", "Ring Road flyover"])
