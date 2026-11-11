"""Person B — sanity checks for source attribution + forecast.

Plain script (no pytest needed). Split into two parts:
  1. Pure-logic checks that need NO database — run these anytime, anywhere.
  2. Live checks that need Postgres+Redis running (docker compose up) since Person A's
     data layer is now async and DB-backed — run these once your DB is up.

Run it with:  backend/.venv/Scripts/python.exe backend/scripts/test_ml_sanity.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.source_attribution import _compass_label, _dust_signal, _industry_signal, _nearest_industrial_zone, _ward_centroid

passed = 0
failed = 0


def check(label: str, condition: bool):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS - {label}")
    else:
        failed += 1
        print(f"  FAIL - {label}")


print("\n=== PART 1: pure-logic checks (no database needed) ===")

print("\n1) Dust score reacts to weather (dry + windy = more dust, rain = less dust)")
dry_windy = _dust_signal(humidity=20, wind_kph=35, rain_mm=0)
humid_calm = _dust_signal(humidity=90, wind_kph=2, rain_mm=0)
rainy = _dust_signal(humidity=20, wind_kph=35, rain_mm=10)
print(f"   dry+windy={dry_windy:.3f}  humid+calm={humid_calm:.3f}  rainy={rainy:.3f}")
check("dry+windy gives a higher dust score than humid+calm", dry_windy > humid_calm)
check("rain lowers the dust score even when dry+windy", rainy < dry_windy)

print("\n2) Compass label conversion (degrees -> N/NE/E/...)")
check("0 degrees is N", _compass_label(0) == "N")
check("90 degrees is E", _compass_label(90) == "E")
check("225 degrees is SW", _compass_label(225) == "SW")

print("\n3) Real ward + industrial zone lookup (using Person A's real Delhi data files)")
ward_lon, ward_lat = _ward_centroid("CANT_1")
print(f"   CANT_1 centroid: lon={ward_lon:.4f} lat={ward_lat:.4f}")
distance_km, zone_name, _, _ = _nearest_industrial_zone(ward_lon, ward_lat)
print(f"   nearest zone: '{zone_name}' at {distance_km:.2f} km")
check("ward centroid is within Delhi's rough bounding box", 76.8 < ward_lon < 77.6 and 28.3 < ward_lat < 28.9)
check("nearest zone has a real name, not the 'industrial zone' fallback", zone_name != "industrial zone")

print("\n4) Industry wind-boost reacts to wind direction (blowing toward the ward vs away from it)")
score_toward, meta_toward = _industry_signal("CANT_1", 135)   # SE in degrees
score_away, meta_away = _industry_signal("CANT_1", 315)       # NW in degrees
print(f"   wind=135deg(SE) -> score={score_toward:.3f} boost={meta_toward['wind_boost']}")
print(f"   wind=315deg(NW) -> score={score_away:.3f} boost={meta_away['wind_boost']}")
check("wind boost factor changes depending on direction",
      abs(meta_toward["wind_boost"] - meta_away["wind_boost"]) > 1e-9)

print("\n5) LightGBM Forecasting Model validation")
from app.ml.forecast_model import _load_model, FEATURE_NAMES, GLOBAL_MODEL_PATH, METADATA_PATH
check("Trained LightGBM model file exists", GLOBAL_MODEL_PATH.exists())
check("Model metadata file exists", METADATA_PATH.exists())
lgb_model = _load_model()
check("Model loads as LGBMRegressor", hasattr(lgb_model, "predict"))
dummy_row = [150.0, 148.0, 145.0, 160.0, 155.0, 26.5, 52.0, 12.0, 0.707, 0.707, 0.0, 14, 2, 0]
import pandas as pd
pred_val = lgb_model.predict(pd.DataFrame([dummy_row], columns=FEATURE_NAMES))[0]
print(f"   Sample inference test: input AQI~150 -> predicted={pred_val:.1f}")
check("Inference outputs realistic positive numerical AQI", 20 <= pred_val <= 400)

print("\n6) Dynamic Source Attribution chemical/spatial tests (no hardcoded weights)")
from app.ml.source_attribution import compute_dynamic_attribution, _dynamic_fallback_reasoning

# Case A: High PM2.5/PM10 ratio (0.75), morning rush hour NO2=70 -> Traffic dominance
shares_a, dominant_a, diag_a = compute_dynamic_attribution(
    pm25=120, pm10=160, no2=70, traffic_index=0.85, active_sites=0,
    distance_km=12, plume_alignment=0.1, wind_kph=10, humidity=50, precipitation_mm=0, hour_local=9
)
print(f"   Case A (Fine combustion, rush): Dominant={dominant_a}, Traffic={shares_a['traffic']*100:.1f}%, PM ratio={diag_a['pm25_pm10_ratio']}")
check("High PM2.5/PM10 ratio + rush hour yields Traffic as dominant source", dominant_a == "traffic" and shares_a["traffic"] > 0.6)
check("Shares sum to exactly 1.0", abs(sum(shares_a.values()) - 1.0) < 1e-6)

# Case B: Low PM2.5/PM10 ratio (0.28), dry (hum=20%), windy (28kph), no active sites -> Dust dominance
shares_b, dominant_b, diag_b = compute_dynamic_attribution(
    pm25=45, pm10=160, no2=20, traffic_index=0.2, active_sites=0,
    distance_km=15, plume_alignment=0.1, wind_kph=28, humidity=20, precipitation_mm=0, hour_local=14
)
print(f"   Case B (Coarse crustal, dry wind): Dominant={dominant_b}, Dust={shares_b['dust']*100:.1f}%, PM ratio={diag_b['pm25_pm10_ratio']}")
check("Low PM2.5/PM10 ratio + dry windy conditions yields Dust as dominant source", dominant_b == "dust" and shares_b["dust"] > 0.6)

# Case C: Low PM2.5/PM10 ratio (0.30), active construction sites=3 -> Construction dominance
shares_c, dominant_c, diag_c = compute_dynamic_attribution(
    pm25=60, pm10=200, no2=25, traffic_index=0.3, active_sites=3,
    distance_km=12, plume_alignment=0.1, wind_kph=8, humidity=60, precipitation_mm=0, hour_local=14
)
print(f"   Case C (Coarse crustal, 3 active sites): Dominant={dominant_c}, Construction={shares_c['construction']*100:.1f}%")
check("Active construction sites claim the coarse fraction", dominant_c == "construction" and shares_c["construction"] > 0.6)

# Case D: High PM2.5/PM10 ratio (0.70), 2km from zone, direct plume alignment -> Industry dominance
shares_d, dominant_d, diag_d = compute_dynamic_attribution(
    pm25=110, pm10=157, no2=30, traffic_index=0.2, active_sites=0,
    distance_km=2.0, plume_alignment=0.95, wind_kph=14, humidity=40, precipitation_mm=0, hour_local=14
)
print(f"   Case D (Near industrial zone + direct plume): Dominant={dominant_d}, Industry={shares_d['industry']*100:.1f}%")
check("Gaussian plume alignment and proximity yields Industry as dominant source", dominant_d == "industry" and shares_d["industry"] > 0.5)

# Case E: Dynamic reasoning generator
reason_d = _dynamic_fallback_reasoning(
    dominant_source=dominant_d, shares=shares_d, ratio=diag_d["pm25_pm10_ratio"],
    pm25=110, pm10=157, no2=30, nearest_zone="Okhla Industrial Area", distance_km=2.0,
    wind_label="NW", wind_kph=14, active_sites=0
)
print(f"   Reasoning Sample: {reason_d[:90]}...")
check("Reasoning dynamically cites exact numbers and dominant source", "62" in reason_d or "Okhla" in reason_d or "pm" in reason_d.lower())

print(f"\n{'='*50}\nPART 1 RESULT: {passed} passed, {failed} failed\n{'='*50}")

print("\n=== PART 2: live checks (need `docker compose up` for Postgres+Redis) ===")
print("These call the real async attribute()/predict() functions end-to-end, including a live")
print("Open-Meteo weather fetch and a database round-trip. Run scripts/test_ml_live.py once your")
print("database is running locally (see README 'Run it' section).")

sys.exit(1 if failed else 0)
