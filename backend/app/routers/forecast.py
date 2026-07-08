# TODO: Person B — AQI Prediction. Owns DOCX Section 6 endpoint /api/predict.
# Returns MOCK forecast now; swap internals for app.ml.forecast_model.predict().
from fastapi import APIRouter, Query

from app.models.schemas import ForecastPoint, ForecastResponse

router = APIRouter(prefix="/api", tags=["forecast (Person B)"])


@router.get("/predict", response_model=ForecastResponse)
def predict(
    ward: str = Query(..., description="ward_id"),
    horizon: int = Query(24, description="Hours ahead: 24 | 48 | 72"),
):
    """24/48/72h AQI forecast array. TODO: Person B — Prophet (XGBoost fallback) on historical AQI + weather."""
    base = 180
    points = [
        ForecastPoint(
            timestamp=f"2026-07-06T{h % 24:02d}:00:00Z",
            predicted_aqi=base + (h * 2) % 60,
            trend="rising" if h % 3 else "stable",
            lower=base - 20,
            upper=base + 40,
        )
        for h in range(1, horizon + 1)
    ]
    return ForecastResponse(ward_id=ward, horizon_hours=horizon, points=points, model="mock")
