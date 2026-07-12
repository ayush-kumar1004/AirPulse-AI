# Citizen Health Advisor agent.
import json
import logging

from app.llm.data_bridge import fetch_aqi, fetch_forecast, fetch_weather
from app.llm.llm_client import get_llm

logger = logging.getLogger(__name__)


def _clean_and_parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def advise(ward_id: str, language: str = "en", profile: str | None = None) -> dict:
    """Return {'ward_id','language','advice','aqi','best_outdoor_window','worst_outdoor_window'} — personalised health guidance."""
    # 1. Fetch current AQI and weather
    try:
        aqi_data = fetch_aqi(ward_id)
        weather_data = fetch_weather(ward_id)
        forecast_points = fetch_forecast(ward_id, 24)
    except Exception as e:
        logger.error(f"Error fetching data for citizen advisor in ward {ward_id}: {e}", exc_info=True)
        # sensible fallback
        return {
            "ward_id": ward_id,
            "language": language,
            "aqi": 180,
            "advice": "Air quality is poor today. Wear an N95 mask outside, keep windows closed, and limit strenuous activities." if language != "hi" else "आज वायु गुणवत्ता खराब है। कृपया बाहर जाते समय N95 मास्क पहनें, खिड़कियां बंद रखें और बाहरी गतिविधियों को सीमित करें।",
            "best_outdoor_window": "15:00-17:00",
            "worst_outdoor_window": "07:00-10:00"
        }

    # Normalize user profile and language name
    user_profile = profile or "general public"
    lang_map = {
        "en": "English",
        "hi": "Hindi",
        "pa": "Punjabi",
        "bn": "Bengali",
    }
    lang_name = lang_map.get(language.lower(), language)

    context_str = f"""
Ward ID: {ward_id}
Ward Name: {aqi_data['ward_name']}
Current AQI: {aqi_data['aqi']} ({aqi_data['category']})
PM2.5: {aqi_data['pm25']} µg/m³, PM10: {aqi_data['pm10']} µg/m³, NO2: {aqi_data['no2']} µg/m³
User Profile/Conditions: {user_profile}
Target Output Language for advice: {lang_name} (code: {language})

Local Weather:
- Temperature: {weather_data.get('temp_c')} °C
- Wind Speed: {weather_data.get('wind_kph')} kph
- Wind Direction: {weather_data.get('wind_dir')}
- Humidity: {weather_data.get('humidity')}%

AQI 24h Forecast points:
{json.dumps(forecast_points[:8], indent=2)}
"""

    system_prompt = f"""You are a warm, reassuring, and expert public health communication advisor translating air quality data into plain, friendly advice for a citizen in Delhi.
Your goal is to provide personalized, multilingual health guidance based on their profile, current AQI, and forecast.

You MUST write the main advice text directly in the requested language: {lang_name}. The advice should be clear, warm, and easy to understand for ordinary citizens.

SAFETY FACTS YOU MUST CONFLICT-FREE ENFORCE:
1. If the current AQI is > 150, advise wearing an N95 mask outdoors.
2. If the user profile indicates 'asthma' and current AQI is > 150, advise them to strictly avoid outdoor activity, especially during early morning and late evening rush hours.
3. Joggers/fitness enthusiasts should shift high-intensity outdoor activities (like jogging) to times when AQI is lowest (typically late afternoon).
4. If AQI is > 300, advise everyone, especially children and elderly, to limit outdoor exposure entirely and keep indoor windows closed.

Always treat these guidelines as vetted facts. Do not contradict them under any circumstances.

Output must be in JSON format matching this schema:
{{
  "ward_id": "string",
  "language": "string",
  "aqi": int,
  "advice": "string (warm, friendly health advice in {lang_name}, tailored to their profile and the AQI level, citing outdoor rules and N95 masks where appropriate)",
  "best_outdoor_window": "string (e.g. '15:00-17:00' - the slot with lowest forecasted AQI)",
  "worst_outdoor_window": "string (e.g. '07:00-10:00' - the slot with highest forecasted AQI)"
}}

DO NOT include any markdown code blocks, note text, or preamble. Return ONLY raw valid JSON."""

    try:
        llm = get_llm(provider="gemini", temperature=0.0)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the context data:\n{context_str}"}
        ]
        response = llm.invoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        parsed = _clean_and_parse_json(content)

        # Enforce schemas
        parsed["ward_id"] = ward_id
        parsed["language"] = language
        parsed["aqi"] = aqi_data["aqi"]

        return parsed
    except Exception as e:
        logger.error(f"Error in citizen advisor LLM execution for ward {ward_id}: {e}", exc_info=True)
        # safe fallback
        fallback_advice = "AQI is elevated today. Please wear an N95 mask outdoors, keep windows closed, and limit strenuous activities."
        if language == "hi":
            fallback_advice = "आज वायु गुणवत्ता खराब है। कृपया बाहर जाते समय N95 मास्क पहनें, खिड़कियां बंद रखें और बाहरी गतिविधियों को सीमित करें।"
        elif language == "pa":
            fallback_advice = "ਅੱਜ ਹਵਾ ਦੀ ਗੁਣਵੱਤਾ ਖ਼ਰਾਬ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਬਾਹਰ ਜਾਣ ਵੇਲੇ N95 ਮਾਸਕ ਪਹਿਨੋ, ਖਿੜਕੀਆਂ ਬੰਦ ਰੱਖੋ ਅਤੇ ਬਾਹਰੀ ਗਤੀਵਿਧੀਆਂ ਨੂੰ ਸੀਮਤ ਕਰੋ।"
        return {
            "ward_id": ward_id,
            "language": language,
            "aqi": aqi_data["aqi"],
            "advice": fallback_advice,
            "best_outdoor_window": "15:00-17:00",
            "worst_outdoor_window": "07:00-10:00"
        }
