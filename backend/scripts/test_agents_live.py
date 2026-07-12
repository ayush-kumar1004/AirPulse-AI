"""Person C — live end-to-end check for the agent layer.

Needs Postgres + Redis running (docker compose up) AND a real LLM API key set in backend/.env
(GEMINI_API_KEY preferred, falls back to ANTHROPIC_API_KEY/OPENAI_API_KEY/KIMI_API_KEY).

Run it with:  backend/.venv/Scripts/python.exe backend/scripts/test_agents_live.py [ward_id]
Defaults to ward_id "CANT_1" (a real Delhi ward from Person A's wards.geojson).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.llm.citizen_advisor import advise
from app.llm.officer_chat import chat
from app.llm.recommendation_agent import recommend_actions


def main(ward_id: str):
    print(f"Recommendation for ward '{ward_id}'...")
    print(json.dumps(recommend_actions(ward_id), indent=2, default=str))

    print(f"\nCitizen advisory for ward '{ward_id}' (Hindi, asthma)...")
    print(json.dumps(advise(ward_id, language="hi", profile="asthma"), indent=2, default=str))

    print(f"\nOfficer chat: 'Why is {ward_id} polluted today?'...")
    print(json.dumps(chat(f"Why is {ward_id} polluted today?", ward_id), indent=2, default=str))


if __name__ == "__main__":
    ward = sys.argv[1] if len(sys.argv) > 1 else "CANT_1"
    main(ward)
