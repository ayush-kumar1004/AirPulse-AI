"""Person B — TRANSPARENT weighted-scoring source attribution (NOT a black-box classifier).

Combines four raw signals into a percentage split across traffic / construction / industry / dust:
  - traffic_index        <- Person A, /api/traffic (SIMULATED)
  - active_sites         <- Person A, /api/construction (SIMULATED)
  - industry proximity   <- static industrial_zones.geojson + ward centroid distance
  - wind direction/speed <- Person A, /api/weather (REAL, Open-Meteo)
  - dust heuristic        <- derived from humidity/wind/rain (no direct dust sensor exists)

Every number here can be explained to a judge — that is the point of choosing a weighted
scoring model over a black-box classifier.
"""
import json
import math
from pathlib import Path

from app.routers.data import construction as construction_ep
from app.routers.data import traffic as traffic_ep
from app.routers.data import weather as weather_ep

WARDS_PATH = Path(__file__).resolve().parent.parent / "data" / "wards.geojson"
INDUSTRIAL_ZONES_PATH = Path(__file__).resolve().parent.parent / "data" / "industrial_zones.geojson"

# Starting weights from domain research (traffic typically 30-45% in Indian cities at rush hour).
# Tune these during the build if a demo scenario needs it — keep the change small and explainable.
BASE_WEIGHTS = {"traffic": 0.40, "construction": 0.25, "industry": 0.20, "dust": 0.15}

WIND_COMPASS_DEGREES = {
    "N": 0, "NE": 45, "E": 90, "SE": 135,
    "S": 180, "SW": 225, "W": 270, "NW": 315,
}


def _polygon_centroid(coordinates) -> tuple[float, float]:
    """Plain average of the outer ring's points — good enough at ward scale, no GIS libs needed."""
    ring = coordinates[0]
    lon = sum(p[0] for p in ring) / len(ring)
    lat = sum(p[1] for p in ring) / len(ring)
    return lon, lat


def _load_geojson(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ward_centroid(ward_id: str) -> tuple[float, float]:
    data = _load_geojson(WARDS_PATH)
    for feature in data["features"]:
        if feature["properties"]["ward_id"] == ward_id:
            return _polygon_centroid(feature["geometry"]["coordinates"])
    # Ward not found in the placeholder file yet — fall back to a fixed Delhi-ish point.
    return 77.20, 28.61


def _nearest_industrial_zone(ward_lon: float, ward_lat: float) -> tuple[float, str]:
    """Return (distance_km, zone_name) to the closest industrial zone."""
    data = _load_geojson(INDUSTRIAL_ZONES_PATH)
    best_km, best_name = float("inf"), "none"
    for feature in data["features"]:
        zlon, zlat = _polygon_centroid(feature["geometry"]["coordinates"])
        # Flat-earth approx is fine at city scale: 1 degree latitude ~= 111 km.
        km = math.hypot((zlon - ward_lon) * 96, (zlat - ward_lat) * 111)
        if km < best_km:
            best_km, best_name = km, feature["properties"].get("zone_name", "industrial zone")
    return best_km, best_name


def _bearing_deg(from_lon, from_lat, to_lon, to_lat) -> float:
    """Compass bearing (0=N, 90=E) from one point to another."""
    dx, dy = to_lon - from_lon, to_lat - from_lat
    return (90 - math.degrees(math.atan2(dy, dx))) % 360


def _industry_signal(ward_id: str, wind_dir: str | None) -> tuple[float, dict]:
    ward_lon, ward_lat = _ward_centroid(ward_id)
    distance_km, zone_name = _nearest_industrial_zone(ward_lon, ward_lat)

    # Proximity score: 1.0 right next to a zone, fading to 0 by ~10km out.
    proximity = max(0.0, 1 - distance_km / 10)

    # Wind boost: if wind blows FROM the zone's direction TOWARD the ward, pollution carries over.
    boost = 1.0
    if wind_dir and wind_dir in WIND_COMPASS_DEGREES:
        data = _load_geojson(INDUSTRIAL_ZONES_PATH)
        zlon, zlat = _polygon_centroid(data["features"][0]["geometry"]["coordinates"])
        bearing_ward_to_zone = _bearing_deg(ward_lon, ward_lat, zlon, zlat)
        wind_deg = WIND_COMPASS_DEGREES[wind_dir]
        alignment = math.cos(math.radians(bearing_ward_to_zone - wind_deg))  # 1 = perfectly aligned
        boost = 1 + 0.6 * max(0.0, alignment)

    score = min(proximity * boost, 1.0)
    return score, {"nearest_zone": zone_name, "distance_km": round(distance_km, 2), "wind_boost": round(boost, 2)}


def _dust_signal(weather: dict) -> float:
    """No direct dust sensor exists, so approximate: dry + windy + no rain raises dust."""
    humidity = weather.get("humidity", 50)
    wind_kph = weather.get("wind_kph", 5)
    rain_mm = weather.get("rain_mm", 0)
    dust = (1 - humidity / 100) * 0.5 + min(wind_kph / 40, 1) * 0.5 - min(rain_mm / 5, 1) * 0.3
    return max(0.0, min(dust, 1.0))


def _confidence(traffic_note: str, construction_note: str, weather: dict) -> float:
    """Lower confidence when an input feeding the score is simulated rather than real."""
    confidence = 0.90
    if "SIMULATED" in traffic_note:
        confidence -= 0.08
    if "SIMULATED" in construction_note:
        confidence -= 0.06
    if not weather.get("wind_dir"):
        confidence -= 0.10
    return round(max(0.5, min(confidence, 0.95)), 2)


def _reasoning(shares: dict, industry_meta: dict, weather: dict) -> str:
    dominant = max(shares, key=shares.get)
    parts = [f"{k.title()} contributes {v*100:.0f}%" for k, v in sorted(shares.items(), key=lambda kv: -kv[1])]
    text = f"{dominant.title()} is the dominant source. " + "; ".join(parts) + "."
    if shares["industry"] > 0.15:
        text += (f" Wind ({weather.get('wind_dir', 'n/a')} at {weather.get('wind_kph', '?')} kph) is carrying "
                 f"pollution from {industry_meta['nearest_zone']} ({industry_meta['distance_km']} km away).")
    return text


def attribute(ward_id: str) -> dict:
    """Return {'ward_id','traffic','construction','industry','dust','confidence','raw_factors','reasoning'}."""
    traffic_data = traffic_ep(ward_id)
    construction_data = construction_ep(ward_id)
    weather_data = weather_ep(ward_id)

    traffic_score = traffic_data.traffic_index
    construction_score = min(construction_data.active_sites / 3, 1.0)
    industry_score, industry_meta = _industry_signal(ward_id, weather_data.get("wind_dir"))
    dust_score = _dust_signal(weather_data)

    raw = {"traffic": traffic_score, "construction": construction_score,
           "industry": industry_score, "dust": dust_score}
    weighted = {k: raw[k] * BASE_WEIGHTS[k] for k in BASE_WEIGHTS}
    total = sum(weighted.values()) or 1e-9
    shares = {k: round(v / total, 3) for k, v in weighted.items()}

    confidence = _confidence(traffic_data.note, construction_data.note, weather_data)
    reasoning = _reasoning(shares, industry_meta, weather_data)

    return {
        "ward_id": ward_id,
        "traffic": shares["traffic"],
        "construction": shares["construction"],
        "industry": shares["industry"],
        "dust": shares["dust"],
        "confidence": confidence,
        "raw_factors": {
            "traffic_index": traffic_score,
            "construction_sites": construction_data.active_sites,
            **industry_meta,
            "wind_dir": weather_data.get("wind_dir"),
            "wind_kph": weather_data.get("wind_kph"),
            "dust_index": round(dust_score, 3),
        },
        "reasoning": reasoning,
    }
