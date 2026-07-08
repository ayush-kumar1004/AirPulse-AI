"""Person B — AQI forecasting: 24/48/72h per ward.

Tries Prophet first (handles daily/weekly seasonality with almost no feature engineering — the
doc's recommended starting point). If Prophet is not installed or training data is missing, falls
back to a simple seasonal-persistence formula so the API never breaks mid-demo.

Until Person A's real historical AQI pipeline is live, `_synthetic_history()` stands in so this
module can be built and tested independently — swap it for a real DB query once ready, everything
downstream (train/predict/API shape) stays the same.
"""
import math
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import pandas as pd

from app.routers.data import current_aqi

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

MODELS_DIR = Path(__file__).resolve().parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def _synthetic_history(ward_id: str, days: int = 30) -> pd.DataFrame:
    """PLACEHOLDER training data — deterministic daily/weekly pattern + noise.
    TODO: swap for real historical AQI once Person A's ingestion/DB is ready
    (same shape: columns 'ds' timestamp, 'y' aqi value)."""
    base = current_aqi(ward_id).aqi
    rows = []
    start = datetime(2026, 6, 1)
    for h in range(days * 24):
        ts = start + timedelta(hours=h)
        daily_cycle = 30 * math.sin((ts.hour - 6) / 24 * 2 * math.pi)      # worse mornings/evenings
        weekly_cycle = -15 if ts.weekday() >= 5 else 0                     # cleaner on weekends
        noise = ((h * 37) % 23) - 11                                       # deterministic pseudo-noise
        rows.append({"ds": ts, "y": max(20, base + daily_cycle + weekly_cycle + noise)})
    return pd.DataFrame(rows)


def _model_path(ward_id: str) -> Path:
    return MODELS_DIR / f"{ward_id}_prophet.pkl"


def train(ward_id: str, history: pd.DataFrame | None = None) -> None:
    """Fit and persist a Prophet model for a ward. No-op if Prophet isn't installed."""
    if not PROPHET_AVAILABLE:
        return
    df = history if history is not None else _synthetic_history(ward_id)
    model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
    model.fit(df)
    joblib.dump(model, _model_path(ward_id))


def _fallback_predict(ward_id: str, horizon_hours: int) -> list[dict]:
    """No trained model available — a sensible seasonal-persistence estimate, never crashes."""
    base = current_aqi(ward_id).aqi
    points = []
    now = datetime.utcnow()
    for h in range(1, horizon_hours + 1):
        ts = now + timedelta(hours=h)
        daily_cycle = 25 * math.sin((ts.hour - 6) / 24 * 2 * math.pi)
        value = max(15, round(base + daily_cycle))
        prev = points[-1]["predicted_aqi"] if points else base
        trend = "rising" if value > prev else "falling" if value < prev else "stable"
        points.append({
            "timestamp": ts.strftime("%Y-%m-%dT%H:00:00Z"),
            "predicted_aqi": value,
            "trend": trend,
            "lower": max(10, value - 25),
            "upper": value + 25,
        })
    return points


def predict(ward_id: str, horizon_hours: int) -> list[dict]:
    """Return [{'timestamp','predicted_aqi','trend','lower','upper'}, ...] for the next horizon_hours."""
    if not PROPHET_AVAILABLE:
        return _fallback_predict(ward_id, horizon_hours)

    model_path = _model_path(ward_id)
    if not model_path.exists():
        train(ward_id)  # first call for this ward — train once, then reuse the saved model
    if not model_path.exists():
        return _fallback_predict(ward_id, horizon_hours)

    model = joblib.load(model_path)
    future = model.make_future_dataframe(periods=horizon_hours, freq="h", include_history=False)
    forecast = model.predict(future)

    points = []
    prev = None
    for _, row in forecast.iterrows():
        value = max(15, round(row["yhat"]))
        trend = "stable" if prev is None else ("rising" if value > prev else "falling" if value < prev else "stable")
        points.append({
            "timestamp": row["ds"].strftime("%Y-%m-%dT%H:00:00Z"),
            "predicted_aqi": value,
            "trend": trend,
            "lower": max(10, round(row["yhat_lower"])),
            "upper": round(row["yhat_upper"]),
        })
        prev = value
    return points


def model_name() -> str:
    return "prophet" if PROPHET_AVAILABLE else "seasonal-fallback"
