"""Person C — sanity checks for government recommendation, citizen health advisor, and officer chat.
Run this script to verify imports and execution of your agent layer.
Run with:
  backend/.venv/Scripts/python.exe backend/scripts/test_agents_sanity.py
"""
import sys
import os
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from app.llm.recommendation_agent import recommend_actions
from app.llm.citizen_advisor import advise
from app.llm.officer_chat import chat as chat_agent

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


# Check API keys
gemini_key = os.environ.get("GEMINI_API_KEY")
anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
openai_key = os.environ.get("OPENAI_API_KEY")

masked_gemini = f"{gemini_key[:4]}...{gemini_key[-4:]}" if gemini_key else "None"
print(f"Configured Keys: GEMINI_API_KEY={masked_gemini}, ANTHROPIC_API_KEY={bool(anthropic_key)}, OPENAI_API_KEY={bool(openai_key)}")

if gemini_key:
    import requests
    print("\n--- Diagnostic: Testing raw Google AI Studio endpoints ---")
    headers = {
        "Authorization": f"Bearer {gemini_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gemini-3.5-flash",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    for version in ["v1beta", "v1"]:
        url = f"https://generativelanguage.googleapis.com/{version}/openai/chat/completions"
        try:
            r = requests.post(url, json=payload, headers=headers)
            print(f"  [{version} Endpoint] Status: {r.status_code}")
            print(f"  Response: {r.text[:300]}")
        except Exception as e:
            print(f"  [{version} Endpoint] Failed: {e}")
    print("----------------------------------------------------------\n")

if not (gemini_key or anthropic_key or openai_key):
    print("\nWARNING: No API keys configured in environment. LLM calls will fail or trigger fallbacks.")

print("\n1) Testing Government Action Recommendation Agent...")
try:
    rec_res = recommend_actions("W01")
    print(f"   Ward: {rec_res.get('ward_id')}")
    print(f"   Actions recommended: {len(rec_res.get('actions', []))}")
    for act in rec_res.get("actions", [])[:2]:
        print(f"     - [{act.get('urgency').upper()}] {act.get('action')} on {act.get('target')} (Reason: {act.get('reason')})")
    
    check("recommend_actions returns ward_id", rec_res.get("ward_id") == "W01")
    check("recommend_actions returns actions list", isinstance(rec_res.get("actions"), list))
    check("recommend_actions actions list is not empty", len(rec_res.get("actions", [])) > 0)
    check("recommend_actions returns inspection_priority list", isinstance(rec_res.get("inspection_priority"), list))
except Exception as e:
    failed += 1
    print(f"  FAIL - Government Recommendation Agent threw exception: {e}")

print("\n2) Testing Citizen Health Advisor (Multilingual English/Hindi)...")
try:
    # Test English
    adv_en = advise("W01", language="en", profile="asthma")
    print("   [English Advice]:", adv_en.get("advice"))
    print(f"     Window - Best: {adv_en.get('best_outdoor_window')} | Worst: {adv_en.get('worst_outdoor_window')}")
    check("English advise returns correct ward", adv_en.get("ward_id") == "W01")
    check("English advise returns advice text", len(adv_en.get("advice", "")) > 0)
    check("English advise returns outdoor windows", bool(adv_en.get("best_outdoor_window")))

    # Test Hindi
    adv_hi = advise("W02", language="hi", profile="jogger")
    print("   [Hindi Advice]:", adv_hi.get("advice"))
    check("Hindi advise returns advice text", len(adv_hi.get("advice", "")) > 0)
except Exception as e:
    failed += 1
    print(f"  FAIL - Citizen Health Advisor Agent threw exception: {e}")

print("\n3) Testing Officer Chat Agent (Tool-Using ReAct)...")
try:
    chat_res = chat_agent("Why is Rohini polluted today? Inspect the source attribution and check the weather.", ward_id="W02")
    print("   [Reply]:", chat_res.get("reply"))
    print("   [Tools Used]:", chat_res.get("tools_used"))
    
    check("chat agent returns reply text", len(chat_res.get("reply", "")) > 0)
    check("chat agent reports tools used", isinstance(chat_res.get("tools_used"), list))
    # It should have called at least one tool
    check("chat agent used tools", len(chat_res.get("tools_used", [])) > 0)
except Exception as e:
    failed += 1
    print(f"  FAIL - Officer Chat Agent threw exception: {e}")

print(f"\n{'='*40}\nRESULT: {passed} passed, {failed} failed\n{'='*40}")
sys.exit(1 if failed else 0)
