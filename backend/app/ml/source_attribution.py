"""Upgraded Dynamic Atmospheric & Chemical Source Attribution Engine.

Replaces fixed weights with:
  1. Pollutant Ratio Partitioning:
     - PM2.5/PM10 ratio separates fine combustion aerosols (vehicles, industrial stacks)
       from coarse crustal mechanically-generated particles (road dust, construction).
  2. NO2 Chemical Tracer & Diurnal Rush Hour:
     - Detects internal combustion vehicle emissions during morning and evening rush.
  3. Gaussian Plume Dispersion Model:
     - Computes atmospheric plume transport from Delhi industrial clusters based on
       distance attenuation and Gaussian crosswind angle deviation.
  4. Meteorological Crustal Resuspension:
     - Evaluates surface dryness, ground wind speed, and precipitation washout.
  5. Real LLM-Generated Natural Language Reasoning:
     - Synthesizes exact chemical ratios and dispersion physics via LLM.
"""
import asyncio
import json
import logging
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.data_ingestion.aqi_ingest import get_aqi
from app.data_ingestion.synthetic import get_construction, get_traffic
from app.data_ingestion.weather_ingest import get_weather
from app.llm.llm_client import run_with_failover

logger = logging.getLogger(__name__)

WARDS_PATH = Path(__file__).resolve().parent.parent / "data" / "wards.geojson"
INDUSTRIAL_ZONES_PATH = Path(__file__).resolve().parent.parent / "data" / "industrial_zones.geojson"

COMPASS_LABELS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# In-process cache to keep real-time requests fast and bound LLM calls
_CACHE_SECONDS = 15 * 60
_attribution_cache: dict[str, tuple[float, dict]] = {}


def _compass_label(degrees: float | None) -> str:
    """Nearest 8-point compass label."""
    if degrees is None:
        return "N/A"
    return COMPASS_LABELS[round(degrees / 45) % 8]


def _polygon_centroid(coordinates) -> tuple[float, float]:
    """Plain average of the polygon outer ring points."""
    ring = coordinates[0]
    lon = sum(p[0] for p in ring) / len(ring)
    lat = sum(p[1] for p in ring) / len(ring)
    return lon, lat


def _load_geojson(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ward_centroid(ward_id: str) -> tuple[float, float]:
    """Resolve ward centroid from GeoJSON."""
    try:
        data = _load_geojson(WARDS_PATH)
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            if props.get("ward_id") == ward_id or props.get("id") == ward_id:
                return _polygon_centroid(feature["geometry"]["coordinates"])
    except Exception as e:
        logger.warning(f"Error loading centroid for ward {ward_id}: {e}")
    # Default Delhi centroid fallback
    return 77.20, 28.61


def _nearest_industrial_zone(ward_lon: float, ward_lat: float) -> tuple[float, str, float, float]:
    """Return (distance_km, zone_name, zone_lon, zone_lat) for the closest industrial cluster."""
    try:
        data = _load_geojson(INDUSTRIAL_ZONES_PATH)
        best_km, best_name, best_lon, best_lat = float("inf"), "none", ward_lon, ward_lat
        for feature in data.get("features", []):
            zlon, zlat = _polygon_centroid(feature["geometry"]["coordinates"])
            # 1 deg lat ~= 111km, 1 deg lon ~= 96km in Delhi
            km = math.hypot((zlon - ward_lon) * 96.0, (zlat - ward_lat) * 111.0)
            if km < best_km:
                best_km = km
                best_name = feature.get("properties", {}).get("name", "industrial cluster")
                best_lon, best_lat = zlon, zlat
        return best_km, best_name, best_lon, best_lat
    except Exception as e:
        logger.warning(f"Error loading industrial zones: {e}")
        return 8.5, "Okhla Industrial Area", 77.27, 28.53


def _bearing_deg(from_lon: float, from_lat: float, to_lon: float, to_lat: float) -> float:
    """Compass bearing in degrees (0=N, 90=E) from point A to point B."""
    dx = to_lon - from_lon
    dy = to_lat - from_lat
    return (90.0 - math.degrees(math.atan2(dy, dx))) % 360.0


def _industry_signal(ward_id: str, wind_deg: float | None) -> tuple[float, dict]:
    """Maintains backward-compatibility with sanity test suite while using Gaussian plume logic."""
    ward_lon, ward_lat = _ward_centroid(ward_id)
    distance_km, zone_name, zone_lon, zone_lat = _nearest_industrial_zone(ward_lon, ward_lat)

    proximity = max(0.0, 1.0 - distance_km / 10.0)

    boost = 1.0
    plume_alignment = 0.5
    if wind_deg is not None:
        bearing_ward_to_zone = _bearing_deg(ward_lon, ward_lat, zone_lon, zone_lat)
        delta_deg = abs(bearing_ward_to_zone - wind_deg) % 360.0
        if delta_deg > 180.0:
            delta_deg = 360.0 - delta_deg
        # Gaussian plume crosswind dispersion (sigma = 40 deg)
        plume_alignment = math.exp(-(delta_deg**2) / (2.0 * (40.0**2)))
        boost = 1.0 + 0.6 * plume_alignment

    score = min(proximity * boost, 1.0)
    return score, {
        "nearest_zone": zone_name,
        "distance_km": round(distance_km, 2),
        "wind_boost": round(boost, 2),
        "plume_alignment": round(plume_alignment, 3),
    }


def _dust_signal(humidity: float, wind_kph: float, rain_mm: float) -> float:
    """Meteorological surface dust resuspension index."""
    dust = (1.0 - humidity / 100.0) * 0.5 + min(wind_kph / 40.0, 1.0) * 0.5 - min(rain_mm / 5.0, 1.0) * 0.3
    return max(0.0, min(dust, 1.0))


def compute_dynamic_attribution(
    pm25: float,
    pm10: float,
    no2: float,
    traffic_index: float,
    active_sites: int,
    distance_km: float,
    plume_alignment: float,
    wind_kph: float,
    humidity: float,
    precipitation_mm: float,
    hour_local: int = 12,
) -> tuple[dict[str, float], str, dict]:
    """Calculate non-hardcoded source shares from pollutant ratios and atmospheric dispersion.

    Returns:
        (shares_dict, dominant_source, diagnostic_factors)
    """
    # 1. PM2.5 / PM10 Ratio Partitioning (Combustion vs Crustal)
    ratio = pm25 / max(pm10, 1.0) if pm10 > 0 else 0.55
    ratio = max(0.15, min(ratio, 0.95))

    # Sigmoidal fine combustion fraction vs coarse crustal fraction
    f_combustion = 1.0 / (1.0 + math.exp(-12.0 * (ratio - 0.52)))
    f_crustal = 1.0 - f_combustion

    # 2. Traffic Chemical & Diurnal Strength
    # NO2 thresholding: 25 ug/m3 is clean background, >60 ug/m3 is heavy traffic exhaust
    f_no2 = min(1.0, max(0.15, no2 / 60.0))
    is_rush_hour = (8 <= hour_local <= 11) or (17 <= hour_local <= 21)
    rush_boost = 1.35 if is_rush_hour else (0.75 if (1 <= hour_local <= 5) else 1.0)
    s_traffic = f_combustion * (0.35 * f_no2 + 0.65 * max(0.2, traffic_index)) * rush_boost

    # 3. Industry Gaussian Plume Dispersion Strength
    dist_decay = math.exp(-distance_km / 6.0)
    wind_transport = min(1.0, (wind_kph + 2.0) / 12.0) * math.exp(-max(0.0, wind_kph - 35.0) / 20.0)
    s_industry = f_combustion * dist_decay * (0.15 + 0.85 * plume_alignment) * wind_transport

    # 4. Construction Coarse Silt Strength
    f_sites = min(1.0, active_sites / 2.5)
    s_construction = f_crustal * (0.15 + 0.85 * f_sites)

    # 5. Crustal Windblown Dust Strength
    f_dry = max(0.1, 1.0 - humidity / 100.0)
    f_wind = min(1.0, wind_kph / 25.0)
    f_rain = max(0.05, 1.0 - min(1.0, precipitation_mm / 3.0))
    s_dust = f_crustal * f_dry * (0.3 + 0.7 * f_wind) * f_rain

    # Dynamic Normalization (No hardcoded base weights!)
    total = s_traffic + s_industry + s_construction + s_dust + 1e-9
    shares = {
        "traffic": round(s_traffic / total, 3),
        "industry": round(s_industry / total, 3),
        "construction": round(s_construction / total, 3),
        "dust": round(s_dust / total, 3),
    }

    # Ensure shares strictly sum to 1.0
    diff = 1.0 - sum(shares.values())
    dominant = max(shares, key=shares.get)
    shares[dominant] = round(shares[dominant] + diff, 3)

    diagnostics = {
        "pm25_pm10_ratio": round(ratio, 3),
        "combustion_affinity": round(f_combustion, 3),
        "crustal_affinity": round(f_crustal, 3),
        "no2_factor": round(f_no2, 3),
        "rush_hour_active": is_rush_hour,
        "plume_alignment_factor": round(plume_alignment, 3),
        "distance_decay": round(dist_decay, 3),
        "dust_dryness_factor": round(f_dry, 3),
    }

    return shares, dominant, diagnostics


def _dynamic_fallback_reasoning(
    dominant_source: str,
    shares: dict[str, float],
    ratio: float,
    pm25: float,
    pm10: float,
    no2: float,
    nearest_zone: str,
    distance_km: float,
    wind_label: str,
    wind_kph: float,
    active_sites: int,
) -> str:
    """Generate dynamic, mathematically grounded explanation when LLM is unavailable."""
    dominant_pct = shares[dominant_source] * 100.0

    if dominant_source == "traffic":
        return (
            f"Vehicular traffic is the dominant pollution driver ({dominant_pct:.1f}%), "
            f"characterized by a fine combustion ratio of {ratio:.2f} (PM2.5 {pm25:.0f} µg/m³, PM10 {pm10:.0f} µg/m³) "
            f"and elevated NO2 levels ({no2:.1f} µg/m³) concentrated along transit corridors."
        )
    elif dominant_source == "industry":
        return (
            f"Industrial stack emissions constitute the primary source ({dominant_pct:.1f}%), "
            f"driven by Gaussian plume advection from {nearest_zone} ({distance_km:.1f} km away) "
            f"under {wind_kph:.1f} km/h {wind_label} winds aligning with fine particulate combustion (PM2.5/PM10: {ratio:.2f})."
        )
    elif dominant_source == "construction":
        return (
            f"Construction and demolition activity is the dominant source ({dominant_pct:.1f}%), "
            f"attributable to {active_sites} active construction sites generating high coarse fraction dust "
            f"(PM2.5/PM10 ratio of {ratio:.2f}, indicating crustal mechanical suspension)."
        )
    else:  # dust
        return (
            f"Surface dust resuspension is the leading contributor ({dominant_pct:.1f}%), "
            f"evidenced by low PM2.5/PM10 ratio ({ratio:.2f}) denoting coarse mechanical particulates "
            f"resuspended by {wind_kph:.1f} km/h ground winds over dry unpaved surfaces."
        )


def _generate_llm_reasoning(
    ward_id: str,
    shares: dict[str, float],
    dominant_source: str,
    pm25: float,
    pm10: float,
    no2: float,
    ratio: float,
    nearest_zone: str,
    distance_km: float,
    wind_label: str,
    wind_kph: float,
    plume_alignment: float,
    active_sites: int,
    humidity: float,
    rain_mm: float,
) -> str:
    """Call LLM via run_with_failover to generate an authoritative scientific explanation."""
    context_str = f"""
Ward ID: {ward_id}
Dominant Pollution Source: {dominant_source.upper()} ({shares[dominant_source]*100:.1f}%)
Source Attribution Breakdown:
- Traffic: {shares['traffic']*100:.1f}%
- Industry: {shares['industry']*100:.1f}%
- Construction: {shares['construction']*100:.1f}%
- Dust: {shares['dust']*100:.1f}%

Atmospheric & Chemical Telemetry:
- PM2.5: {pm25:.1f} µg/m³, PM10: {pm10:.1f} µg/m³
- PM2.5 / PM10 Ratio: {ratio:.2f} ({'Combustion-dominated fine aerosols' if ratio >= 0.55 else 'Crustal/mechanical coarse particles'})
- NO2 Concentration: {no2:.1f} µg/m³ (combustion tracer)
- Nearest Industrial Cluster: {nearest_zone} at {distance_km:.1f} km
- Wind: {wind_kph:.1f} km/h from {wind_label} (Gaussian plume alignment factor: {plume_alignment:.2f})
- Active Construction Sites: {active_sites}
- Weather: Humidity {humidity:.1f}%, Rain {rain_mm:.1f} mm
"""

    system_prompt = (
        "You are an expert environmental atmospheric scientist providing pollution source attribution analysis for Delhi.\n"
        "Based on the provided chemical ratios, meteorological conditions, and Gaussian plume dispersion physics, "
        "write a concise, authoritative 2 to 3 sentence scientific explanation for government officers.\n"
        "Explain WHY the dominant source is leading, citing the specific numbers (e.g. PM2.5/PM10 ratio, NO2 concentration, "
        "or wind-carried industrial plume).\n"
        "Do NOT include markdown formatting, bullet points, introductory preamble, or apologies. Return plain text only."
    )

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the telemetry context:\n{context_str}"},
        ]
        response = run_with_failover(lambda llm: llm.invoke(messages), temperature=0.1)
        content = response.content if hasattr(response, "content") else str(response)
        text = content.strip().replace("```", "").replace("\n\n", " ")
        if len(text) > 20:
            return text
    except Exception as e:
        logger.warning(f"LLM reasoning generation failed ({e}); using physics fallback.", exc_info=False)

    return _dynamic_fallback_reasoning(
        dominant_source=dominant_source,
        shares=shares,
        ratio=ratio,
        pm25=pm25,
        pm10=pm10,
        no2=no2,
        nearest_zone=nearest_zone,
        distance_km=distance_km,
        wind_label=wind_label,
        wind_kph=wind_kph,
        active_sites=active_sites,
    )


def _compute_confidence(
    has_real_aqi: bool,
    has_real_weather: bool,
    traffic_note: str,
    construction_note: str,
) -> float:
    """Calculate confidence based on data fidelity."""
    conf = 0.95
    if not has_real_aqi:
        conf -= 0.15
    if not has_real_weather:
        conf -= 0.10
    if "SIMULATED" in traffic_note:
        conf -= 0.05
    if "SIMULATED" in construction_note:
        conf -= 0.05
    return round(max(0.60, min(conf, 0.98)), 2)


async def attribute(session: AsyncSession, ward_id: str) -> dict:
    """Return dynamic source breakdown:

    {
      'ward_id': str,
      'dominant_source': str,
      'traffic': float,
      'construction': float,
      'industry': float,
      'dust': float,
      'confidence': float,
      'raw_factors': dict,
      'reasoning': str
    }
    """
    now = datetime.now(timezone.utc)

    # Check cache to preserve real-time responsiveness
    cached = _attribution_cache.get(ward_id)
    if cached and (time.monotonic() - cached[0] < _CACHE_SECONDS):
        return cached[1]

    # 1. Ingest real atmospheric readings
    has_real_aqi = True
    has_real_weather = True

    try:
        aqi_reading = await get_aqi(session=session, ward_id=ward_id)
        pm25 = float(aqi_reading.pm25 or 75.0)
        pm10 = float(aqi_reading.pm10 or 140.0)
        no2 = float(aqi_reading.no2 or 35.0)
    except Exception as e:
        logger.warning(f"Could not load AQI reading for ward {ward_id}: {e}")
        has_real_aqi = False
        pm25, pm10, no2 = 80.0, 150.0, 40.0

    try:
        weather_reading = await get_weather(session=session, ward_id=ward_id)
        humidity = float(weather_reading.humidity or 50.0)
        wind_kph = float(weather_reading.wind_speed or 10.0)
        wind_deg = float(weather_reading.wind_direction or 0.0)
        rain_mm = float(weather_reading.precipitation or 0.0)
    except Exception as e:
        logger.warning(f"Could not load weather reading for ward {ward_id}: {e}")
        has_real_weather = False
        humidity, wind_kph, wind_deg, rain_mm = 50.0, 10.0, 315.0, 0.0

    traffic_data = get_traffic(ward_id=ward_id, dt=now)
    construction_data = get_construction(ward_id=ward_id, dt=now)

    # 2. Compute spatial & Gaussian plume variables
    ward_lon, ward_lat = _ward_centroid(ward_id)
    distance_km, nearest_zone, zone_lon, zone_lat = _nearest_industrial_zone(ward_lon, ward_lat)

    bearing_ward_to_zone = _bearing_deg(ward_lon, ward_lat, zone_lon, zone_lat)
    delta_deg = abs(bearing_ward_to_zone - wind_deg) % 360.0
    if delta_deg > 180.0:
        delta_deg = 360.0 - delta_deg
    plume_alignment = math.exp(-(delta_deg**2) / (2.0 * (40.0**2)))

    wind_label = _compass_label(wind_deg)
    local_hour = (now.hour + 5) % 24  # UTC to IST approx hour

    # 3. Dynamic chemical and dispersion scoring
    shares, dominant_source, diagnostics = compute_dynamic_attribution(
        pm25=pm25,
        pm10=pm10,
        no2=no2,
        traffic_index=traffic_data.traffic_index,
        active_sites=construction_data.active_sites,
        distance_km=distance_km,
        plume_alignment=plume_alignment,
        wind_kph=wind_kph,
        humidity=humidity,
        precipitation_mm=rain_mm,
        hour_local=local_hour,
    )

    # 4. Generate LLM explanation off the event loop with bounded timeout
    try:
        reasoning = await asyncio.wait_for(
            asyncio.to_thread(
                _generate_llm_reasoning,
                ward_id=ward_id,
                shares=shares,
                dominant_source=dominant_source,
                pm25=pm25,
                pm10=pm10,
                no2=no2,
                ratio=diagnostics["pm25_pm10_ratio"],
                nearest_zone=nearest_zone,
                distance_km=distance_km,
                wind_label=wind_label,
                wind_kph=wind_kph,
                plume_alignment=plume_alignment,
                active_sites=construction_data.active_sites,
                humidity=humidity,
                rain_mm=rain_mm,
            ),
            timeout=4.0,
        )
    except Exception as e:
        logger.info(f"LLM reasoning timed out or failed ({e}) — falling back to deterministic physics explanation.")
        reasoning = _dynamic_fallback_reasoning(
            dominant_source=dominant_source,
            shares=shares,
            ratio=diagnostics["pm25_pm10_ratio"],
            pm25=pm25,
            pm10=pm10,
            no2=no2,
            nearest_zone=nearest_zone,
            distance_km=distance_km,
            wind_label=wind_label,
            wind_kph=wind_kph,
            active_sites=construction_data.active_sites,
        )

    confidence = _compute_confidence(
        has_real_aqi,
        has_real_weather,
        traffic_data.note,
        construction_data.note,
    )

    result = {
        "ward_id": ward_id,
        "dominant_source": dominant_source,
        "traffic": shares["traffic"],
        "construction": shares["construction"],
        "industry": shares["industry"],
        "dust": shares["dust"],
        "confidence": confidence,
        "raw_factors": {
            "pm25": round(pm25, 1),
            "pm10": round(pm10, 1),
            "no2": round(no2, 1),
            **diagnostics,
            "nearest_zone": nearest_zone,
            "distance_km": round(distance_km, 2),
            "wind_dir": wind_label,
            "wind_deg": round(wind_deg, 1),
            "wind_kph": round(wind_kph, 1),
            "humidity": round(humidity, 1),
            "rain_mm": round(rain_mm, 1),
            "active_construction_sites": construction_data.active_sites,
            "traffic_density_index": round(traffic_data.traffic_index, 2),
        },
        "reasoning": reasoning,
    }

    _attribution_cache[ward_id] = (time.monotonic(), result)
    return result
