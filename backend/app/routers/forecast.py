# Person B — AQI Prediction. Owns DOCX Section 6 endpoint /api/predict.
# Real logic: app.ml.forecast_model.predict() — LightGBM Tabular ML Model.
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.ml.forecast_model import (
    evaluate_forecast_performance,
    get_forecast_model_health,
    model_name,
    predict,
)
from app.models.schemas import ForecastResponse

router = APIRouter(prefix="/api", tags=["forecast (Person B)"])


@router.get("/predict", response_model=ForecastResponse)
async def forecast(
    ward_id: str = Query(...),
    horizon: int = Query(24, description="Hours ahead: 24 | 48 | 72"),
    hours: Optional[int] = Query(None, description="Alias for horizon"),
    session: AsyncSession = Depends(get_db),
):
    """24/48/72h AQI forecast array with top 5 feature importances and explanatory drivers."""
    effective_horizon = hours if hours is not None else horizon
    data = await predict(session, ward_id, effective_horizon)
    return ForecastResponse(**data)


@router.get("/predict/performance")
@router.get("/forecast/performance")
async def model_performance(
    ward_id: str = Query("W01", description="Ward ID for evaluation telemetry slice"),
    eval_days: int = Query(7, description="Evaluation window in days"),
    run_eval: bool = Query(False, description="Trigger active evaluation against recent real observations"),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Report LightGBM model performance (MAE, RMSE, MAPE) and production health check."""
    if run_eval:
        return await evaluate_forecast_performance(session=session, ward_id=ward_id, eval_days=eval_days)
    return get_forecast_model_health()
