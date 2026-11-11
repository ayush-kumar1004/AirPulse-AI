"""Person B — live end-to-end check for source attribution + forecast.

Needs Postgres + Redis running (docker compose up, or your local Postgres with the
.env DATABASE settings pointed at it) since these call the real async, DB-backed
functions from Person A's data layer, including a live Open-Meteo weather fetch.

Run it with:  backend/.venv/Scripts/python.exe backend/scripts/test_ml_live.py [ward_id]
Defaults to ward_id "CANT_1" (a real Delhi ward from Person A's wards.geojson).
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.ml.forecast_model import model_name, predict
from app.ml.source_attribution import attribute


async def main(ward_id: str):
    async with AsyncSessionLocal() as session:
        print(f"Fetching source attribution for ward '{ward_id}'...")
        breakdown = await attribute(session, ward_id)
        print(json.dumps(breakdown, indent=2, default=str))

        print(f"\nFetching 24h forecast for ward '{ward_id}' (model: {model_name()})...")
        forecast_res = await predict(session, ward_id, 24)
        points = forecast_res.get("points", [])
        print(f"Got {len(points)} points. First 3:")
        print(json.dumps(points[:3], indent=2, default=str))
        print(f"Summary reason: {forecast_res.get('summary_reason')}")
        print("Top 5 Feature Drivers:")
        print(json.dumps(forecast_res.get("top_features", []), indent=2, default=str))


if __name__ == "__main__":
    ward = sys.argv[1] if len(sys.argv) > 1 else "CANT_1"
    asyncio.run(main(ward))
