# TODO: Person B — AQI forecasting. Prophet per ward (XGBoost fallback if time allows).
# Train on historical AQI (Person A's aqi_readings) + weather regressors. Cache trained models.
# Called by routers/forecast.py — MUST return points matching schemas.ForecastResponse.


def predict(ward_id: str, horizon_hours: int) -> list[dict]:
    """Return [{'timestamp', 'aqi', 'lower', 'upper'}, ...] for the next `horizon_hours`."""
    raise NotImplementedError("Person B: implement Prophet/XGBoost forecast")


def train(ward_id: str) -> None:
    """Fit and persist a model for a ward from historical data."""
    raise NotImplementedError("Person B: implement training pipeline")
