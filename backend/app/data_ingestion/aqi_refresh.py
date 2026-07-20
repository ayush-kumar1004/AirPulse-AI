"""City-wide AQI refresh: one real reading per ward.

/api/heatmap only reads `aqi_readings`; it never triggers ingestion. Nothing else
filled that table for all wards either — get_aqi() writes a single ward, and only
when the frontend asks for it. So 289 of 290 wards had no reading and the heatmap
returned aqi=0 / "Unknown" for the whole city.

Fetching per ward would mean 290 upstream calls, which is what caused the earlier
rate-limit storm. Instead Open-Meteo accepts comma-separated coordinate lists and
returns one result per point, so the whole city costs a handful of requests.

Each ward is sampled at its own polygon centroid rather than a single city-wide
point, which is what makes the map vary between wards instead of rendering flat.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence, Tuple

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_ingestion.aqi_ingest import OPEN_METEO_AQI_URL, AQIIngestionError
from app.models.db_models import AQIReading, Ward

logger = logging.getLogger(__name__)

# Coordinates per upstream request. Open-Meteo allows many, but a long URL risks a
# 414, so the city is split into a few batches.
BATCH_SIZE = 100

WardPoint = Tuple[str, float, float]  # (ward_id, latitude, longitude)


async def get_ward_centroids(session: AsyncSession) -> List[WardPoint]:
    """Return one representative lat/lon per ward, taken from its polygon centroid."""
    stmt = select(
        Ward.id,
        func.ST_Y(func.ST_Centroid(Ward.geom)),
        func.ST_X(func.ST_Centroid(Ward.geom)),
    )
    result = await session.execute(stmt)
    return [(row[0], float(row[1]), float(row[2])) for row in result]


async def fetch_aqi_for_points(points: Sequence[WardPoint]) -> Dict[str, Dict[str, Any]]:
    """Fetch current AQI for many coordinates, batched. Keyed by ward_id.

    A failed batch is logged and skipped so one bad request cannot wipe out the
    whole refresh.
    """
    readings: Dict[str, Dict[str, Any]] = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for start in range(0, len(points), BATCH_SIZE):
            batch = points[start : start + BATCH_SIZE]
            params = {
                "latitude": ",".join(str(lat) for _, lat, _ in batch),
                "longitude": ",".join(str(lon) for _, _, lon in batch),
                "current": "pm10,pm2_5,nitrogen_dioxide,us_aqi",
            }

            try:
                response = await client.get(OPEN_METEO_AQI_URL, params=params)
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as e:
                logger.warning("AQI batch starting at %s failed: %s", start, e)
                continue

            # A single coordinate returns one object; many return a list.
            entries = payload if isinstance(payload, list) else [payload]
            if len(entries) != len(batch):
                logger.warning(
                    "AQI batch size mismatch: asked for %s points, got %s — skipping batch.",
                    len(batch),
                    len(entries),
                )
                continue

            for (ward_id, _, _), entry in zip(batch, entries):
                current = entry.get("current") or {}
                if current.get("us_aqi") is not None:
                    readings[ward_id] = current

    return readings


def _dominant_pollutant(current: Dict[str, Any]) -> str:
    """Pick the pollutant furthest above its Indian NAAQS 24-hour limit."""
    limits = {"pm2.5": ("pm2_5", 60.0), "pm10": ("pm10", 100.0), "no2": ("nitrogen_dioxide", 80.0)}

    ratios = {
        name: current[key] / limit
        for name, (key, limit) in limits.items()
        if current.get(key) is not None
    }
    return max(ratios, key=ratios.get) if ratios else "unknown"


async def refresh_all_ward_aqi(session: AsyncSession) -> int:
    """Write one fresh AQI reading per ward. Returns the number of rows written."""
    points = await get_ward_centroids(session)
    if not points:
        logger.warning("No wards found — skipping AQI refresh.")
        return 0

    readings = await fetch_aqi_for_points(points)
    if not readings:
        raise AQIIngestionError("AQI refresh fetched no usable readings from Open-Meteo.")

    timestamp = datetime.now(timezone.utc)
    for ward_id, current in readings.items():
        session.add(
            AQIReading(
                ward_id=ward_id,
                timestamp=timestamp,
                aqi_value=float(current["us_aqi"]),
                pm25=current.get("pm2_5"),
                pm10=current.get("pm10"),
                no2=current.get("nitrogen_dioxide"),
                dominant_pollutant=_dominant_pollutant(current),
            )
        )

    await session.commit()
    logger.info("Refreshed AQI for %s of %s wards.", len(readings), len(points))
    return len(readings)


async def aqi_refresh_loop(interval_seconds: int, session_factory) -> None:
    """Refresh city AQI forever, every `interval_seconds`. Errors never kill the loop."""
    while True:
        try:
            async with session_factory() as session:
                await refresh_all_ward_aqi(session)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduled AQI refresh failed — will retry next cycle.")

        await asyncio.sleep(interval_seconds)
