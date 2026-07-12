"""Person C — sanity checks for the agent layer (no database or API key needed).

Checks the parts of the agent layer that don't need a live DB or a live LLM call: JSON cleanup,
AQI categorisation, and compass-label conversion in data_bridge.py. For a full live check (real DB
+ real Gemini/Claude call), see scripts/test_agents_live.py once Postgres is running and an API key
is set in backend/.env.

Run with:  backend/.venv/Scripts/python.exe backend/scripts/test_agents_sanity.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.llm.data_bridge import _categorize, _compass_label
from app.llm.recommendation_agent import _clean_and_parse_json

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


print("\n1) AQI categorisation matches routers/data.py's own scale")
check("50 -> Good", _categorize(50) == "Good")
check("100 -> Satisfactory", _categorize(100) == "Satisfactory")
check("200 -> Moderate", _categorize(200) == "Moderate")
check("300 -> Poor", _categorize(300) == "Poor")
check("400 -> Very Poor", _categorize(400) == "Very Poor")
check("450 -> Severe", _categorize(450) == "Severe")

print("\n2) Compass label conversion (degrees -> N/NE/E/...)")
check("0 degrees is N", _compass_label(0) == "N")
check("90 degrees is E", _compass_label(90) == "E")
check("225 degrees is SW", _compass_label(225) == "SW")

print("\n3) LLM JSON-cleanup strips markdown code fences correctly")
raw = '```json\n{"ward_id": "W02", "actions": []}\n```'
cleaned = _clean_and_parse_json(raw)
check("parses fenced JSON into a dict", isinstance(cleaned, dict))
check("preserves the real content", cleaned.get("ward_id") == "W02")

plain = '{"ward_id": "W02"}'
check("parses plain (non-fenced) JSON too", _clean_and_parse_json(plain)["ward_id"] == "W02")

print(f"\n{'='*50}\nRESULT: {passed} passed, {failed} failed\n{'='*50}")

print("\n=== Not covered here (need a live DB + a real LLM API key) ===")
print("recommend_actions(), advise(), and chat() all call a live Gemini/Claude/GPT model and read")
print("real ward data. Run scripts/test_agents_live.py once Postgres is running (docker compose up)")
print("and GEMINI_API_KEY (or ANTHROPIC_API_KEY/OPENAI_API_KEY) is set in backend/.env.")

sys.exit(1 if failed else 0)
