# Person B — AQI Prediction. Owns DOCX Section 6 endpoint /api/predict.
# Real logic: app.ml.forecast_model.predict() — Prophet if available, safe fallback otherwise.
from fastapi import APIRouter, Query

from app.ml.forecast_model import model_name, predict
from app.models.schemas import ForecastPoint, ForecastResponse

router = APIRouter(prefix="/api", tags=["forecast (Person B)"])


@router.get("/predict", response_model=ForecastResponse)
def forecast(ward: str = Query(..., description="ward_id"), horizon: int = Query(24, description="Hours ahead: 24 | 48 | 72")):
    """24/48/72h AQI forecast array."""
    points = [ForecastPoint(**p) for p in predict(ward, horizon)]
    return ForecastResponse(ward_id=ward, horizon_hours=horizon, points=points, model=model_name())
