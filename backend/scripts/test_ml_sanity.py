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

print(f"\n{'='*50}\nPART 1 RESULT: {passed} passed, {failed} failed\n{'='*50}")

print("\n=== PART 2: live checks (need `docker compose up` for Postgres+Redis) ===")
print("These call the real async attribute()/predict() functions end-to-end, including a live")
print("Open-Meteo weather fetch and a database round-trip. Run scripts/test_ml_live.py once your")
print("database is running locally (see README 'Run it' section).")

sys.exit(1 if failed else 0)
