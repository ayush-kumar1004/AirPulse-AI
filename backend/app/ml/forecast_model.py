"""Person B — AQI forecasting: 24/48/72h per ward.

Tries Prophet first (handles daily/weekly seasonality with almost no feature engineering — the
doc's recommended starting point). If Prophet is not installed, or there isn't enough real history
yet, falls back to a simple seasonal-persistence formula so the API never breaks mid-demo.

Updated to match Person A's async DB layer (feat/data-suchit): real AQI/history now comes from
app.data_ingestion.aqi_ingest (get_aqi, get_aqi_history), both async and needing a DB session.
"""
import logging
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_ingestion.aqi_ingest import get_aqi, get_aqi_history

logger = logging.getLogger(__name__)

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

# Importing Prophet is not the same as being able to use it. In the Docker image it
# imports fine, then raises at construction:
#     AttributeError: 'Prophet' object has no attribute 'stan_backend'
# which is Prophet swallowing a failure to load its compiled Stan model and leaving
# the attribute unset. The ImportError guard above never fires, so /api/predict
# returned 500 instead of using the seasonal fallback this module was built to have.
# Once Prophet fails we record it and stop retrying on every request.
_prophet_broken = False


def _prophet_usable() -> bool:
    return PROPHET_AVAILABLE and not _prophet_broken


def _disable_prophet(exc: Exception, stage: str) -> None:
    """Log why Prophet failed, once, and fall back to the seasonal model from here on."""
    global _prophet_broken
    if not _prophet_broken:
        _prophet_broken = True
        logger.error(
            "Prophet unusable at %s (%s: %s) — serving seasonal-fallback forecasts instead. "
            "This usually means the compiled Stan model is missing from the installed prophet package.",
            stage, type(exc).__name__, exc,
        )

MODELS_DIR = Path(__file__).resolve().parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Prophet needs a reasonable number of points to fit daily+weekly seasonality sensibly.
# Person A's historical backfill isn't built yet, so early on the DB will have very few rows —
# below this count we use the synthetic placeholder instead of training on noise.
MIN_REAL_POINTS_FOR_TRAINING = 48


def _synthetic_history(base_aqi: float, days: int = 30) -> pd.DataFrame:
    """PLACEHOLDER training data — deterministic daily/weekly pattern + noise, seeded off a real
    current AQI reading. Used only until Person A's historical backfill has enough real rows."""
    rows = []
    start = datetime(2026, 6, 1)
    for h in range(days * 24):
        ts = start + timedelta(hours=h)
        daily_cycle = 30 * math.sin((ts.hour - 6) / 24 * 2 * math.pi)      # worse mornings/evenings
        weekly_cycle = -15 if ts.weekday() >= 5 else 0                     # cleaner on weekends
        noise = ((h * 37) % 23) - 11                                       # deterministic pseudo-noise
        rows.append({"ds": ts, "y": max(20, base_aqi + daily_cycle + weekly_cycle + noise)})
    return pd.DataFrame(rows)


def _model_path(ward_id: str) -> Path:
    return MODELS_DIR / f"{ward_id}_prophet.pkl"


async def _training_data(session: AsyncSession, ward_id: str) -> tuple[pd.DataFrame, bool]:
    """Return (history_df, used_real_data). Prefers Person A's real historical AQI; falls back
    to the synthetic generator (seeded off the real current reading) if there isn't enough yet."""
    real_history = await get_aqi_history(session=session, ward_id=ward_id, days=90)
    if len(real_history) >= MIN_REAL_POINTS_FOR_TRAINING:
        df = pd.DataFrame({
            "ds": [r.timestamp.replace(tzinfo=None) for r in real_history],
            "y": [r.aqi_value for r in real_history],
        }).sort_values("ds")
        return df, True

    current = await get_aqi(session=session, ward_id=ward_id)
    return _synthetic_history(current.aqi_value), False


async def train(session: AsyncSession, ward_id: str) -> bool:
    """Fit and persist a Prophet model for a ward. Returns whether real data was used.
    No-op (returns False) if Prophet isn't installed or cannot run."""
    if not _prophet_usable():
        return False
    df, used_real_data = await _training_data(session, ward_id)
    try:
        model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
        model.fit(df)
        joblib.dump(model, _model_path(ward_id))
    except Exception as e:
        _disable_prophet(e, "training")
        return False
    return used_real_data


async def _fallback_predict(session: AsyncSession, ward_id: str, horizon_hours: int) -> list[dict]:
    """No trained model available — a sensible seasonal-persistence estimate, never crashes."""
    current = await get_aqi(session=session, ward_id=ward_id)
    base = current.aqi_value
    points = []
    now = datetime.now(timezone.utc)
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


async def predict(session: AsyncSession, ward_id: str, horizon_hours: int) -> list[dict]:
    """Return [{'timestamp','predicted_aqi','trend','lower','upper'}, ...] for the next horizon_hours."""
    if not _prophet_usable():
        return await _fallback_predict(session, ward_id, horizon_hours)

    model_path = _model_path(ward_id)
    if not model_path.exists():
        await train(session, ward_id)  # first call for this ward — train once, then reuse the saved model
    if not model_path.exists() or not _prophet_usable():
        return await _fallback_predict(session, ward_id, horizon_hours)

    try:
        model = joblib.load(model_path)
        future = model.make_future_dataframe(periods=horizon_hours, freq="h", include_history=False)
        forecast = model.predict(future)
    except Exception as e:
        # A saved model can still fail to load or run — e.g. a stale pickle after a
        # dependency upgrade. Never let that 500 the endpoint.
        _disable_prophet(e, "prediction")
        return await _fallback_predict(session, ward_id, horizon_hours)

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
    return "prophet" if _prophet_usable() else "seasonal-fallback"
