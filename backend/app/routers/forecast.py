# Person B — AQI Prediction. Owns DOCX Section 6 endpoint /api/predict.
# Real logic: app.ml.forecast_model.predict() — Prophet if available, safe fallback otherwise.
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.ml.forecast_model import model_name, predict
from app.models.schemas import ForecastPoint, ForecastResponse

router = APIRouter(prefix="/api", tags=["forecast (Person B)"])


@router.get("/predict", response_model=ForecastResponse)
async def forecast(
    ward_id: str = Query(...),
    horizon: int = Query(24, description="Hours ahead: 24 | 48 | 72"),
    session: AsyncSession = Depends(get_db),
):
    """24/48/72h AQI forecast array."""
    raw_points = await predict(session, ward_id, horizon)
    points = [ForecastPoint(**p) for p in raw_points]
    return ForecastResponse(ward_id=ward_id, horizon_hours=horizon, points=points, model=model_name())
