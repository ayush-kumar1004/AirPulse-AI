"""Person B — sanity checks for source attribution + forecast.

Plain script (no pytest needed) that proves the two things the team's plan calls the
"definition of done" for this track:
  1. The source score reacts sensibly when inputs change (wind, humidity, rain).
  2. The forecast endpoint works cleanly at 24h / 48h / 72h.

Run it with:  backend/.venv/Scripts/python.exe backend/scripts/test_ml_sanity.py
(run from the project root, or adjust the path above to match where your venv lives)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.forecast_model import model_name, predict
from app.ml.source_attribution import _dust_signal, _industry_signal, attribute

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


print("\n1) Dust score reacts to weather (dry + windy = more dust, rain = less dust)")
dry_windy = _dust_signal({"humidity": 20, "wind_kph": 35, "rain_mm": 0})
humid_calm = _dust_signal({"humidity": 90, "wind_kph": 2, "rain_mm": 0})
rainy = _dust_signal({"humidity": 20, "wind_kph": 35, "rain_mm": 10})
print(f"   dry+windy={dry_windy:.3f}  humid+calm={humid_calm:.3f}  rainy={rainy:.3f}")
check("dry+windy gives a higher dust score than humid+calm", dry_windy > humid_calm)
check("rain lowers the dust score even when dry+windy", rainy < dry_windy)

print("\n2) Industry wind-boost reacts to wind direction (blowing toward the ward vs away from it)")
# NOTE: W01 in the placeholder wards.geojson is ~12.5km from the placeholder industrial zone,
# beyond the 10km proximity falloff, so the FINAL score stays 0 either way (0 x anything = 0).
# That's expected placeholder-data behaviour, not a bug — so we check the wind_boost factor
# itself here, which is the part this feature actually controls.
score_toward, meta_toward = _industry_signal("W01", "SE")
score_away, meta_away = _industry_signal("W01", "NW")
print(f"   wind=SE -> score={score_toward:.3f} boost={meta_toward['wind_boost']}")
print(f"   wind=NW -> score={score_away:.3f} boost={meta_away['wind_boost']}")
check("wind boost factor changes depending on direction",
      abs(meta_toward["wind_boost"] - meta_away["wind_boost"]) > 1e-9)

print("\n3) Full attribute() end-to-end still returns a valid, normalised breakdown")
result = attribute("W01")
total_share = result["traffic"] + result["construction"] + result["industry"] + result["dust"]
print(f"   traffic={result['traffic']} construction={result['construction']} "
      f"industry={result['industry']} dust={result['dust']}  (sum={total_share:.3f})")
check("the four shares add up to ~1.0", abs(total_share - 1.0) < 0.01)
check("confidence is between 0 and 1", 0 <= result["confidence"] <= 1)

print(f"\n4) Forecast works at 24h / 48h / 72h (model in use: {model_name()})")
for horizon in (24, 48, 72):
    points = predict("W01", horizon)
    check(f"horizon={horizon} returns exactly {horizon} points", len(points) == horizon)
    check(f"horizon={horizon} every predicted_aqi is a positive number",
          all(p["predicted_aqi"] > 0 for p in points))

print(f"\n{'='*40}\nRESULT: {passed} passed, {failed} failed\n{'='*40}")
sys.exit(1 if failed else 0)
