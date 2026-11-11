"""CLI script to train the LightGBM AQI forecasting model on real historical data.

Usage:
    python backend/scripts/train_forecast_model.py [--days 30] [--ward WARD_ID]

Example:
    python backend/scripts/train_forecast_model.py
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.ml.forecast_model import train


async def main():
    parser = argparse.ArgumentParser(description="Train LightGBM AQI Forecasting Model")
    parser.add_argument("--days", type=int, default=30, help="Number of historical days to train on (default: 30)")
    parser.add_argument("--ward", type=str, default=None, help="Ward ID to train on (default: global Delhi coordinates)")
    args = parser.parse_args()

    print(f"============================================================")
    print(f"Training LightGBM AQI Forecasting Model (days={args.days}, ward={args.ward or 'Delhi Global'})")
    print(f"============================================================")

    try:
        async with AsyncSessionLocal() as session:
            meta = await train(session=session, ward_id=args.ward)
    except Exception as e:
        print(f"[Notice] Database session unavailable ({e}). Training standalone via Open-Meteo...")
        meta = await train(session=None, ward_id=args.ward)

    print("\nTraining Complete!")
    print(f"Model Type:        {meta.get('model_type')}")
    print(f"Trained At:        {meta.get('trained_at')}")
    print(f"Training Samples:  {meta.get('training_samples')} hourly observations")
    print(f"Train RMSE:        {meta.get('rmse')} AQI points")
    print(f"Train MAE:         {meta.get('mae')} AQI points")
    print("\nFeature Importances (Top Drivers):")
    for feat, imp in sorted(meta.get("feature_importances", {}).items(), key=lambda kv: -kv[1]):
        bar = "█" * int(imp * 40)
        print(f"  {feat:15s} : {imp*100:5.1f}% | {bar}")

    print("\nModel saved to backend/app/data/models/lgbm_forecast.joblib")


if __name__ == "__main__":
    asyncio.run(main())

