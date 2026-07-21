# Government Action Recommendation agent.
import json
import logging
import time

from app.llm.data_bridge import fetch_aqi, fetch_construction, fetch_forecast, fetch_source_attribution, fetch_traffic, fetch_weather
from app.llm.llm_client import run_with_failover

logger = logging.getLogger(__name__)

# The /api/recommend route caches in Redis, but the officer-chat agent calls
# recommend_actions() directly as a tool and so bypassed that entirely — one
# chat message could spend several of the free tier's 20 daily requests
# re-deriving the same ward. This in-process cache sits on the function itself,
# so every caller benefits.
_CACHE_SECONDS = 30 * 60
_cache: dict[str, tuple[float, dict]] = {}


def _clean_and_parse_json(text: str) -> dict:
    text = text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def recommend_actions(ward_id: str) -> dict:
    """Return {'ward_id', 'actions': [...], 'inspection_priority': [...]} — prioritised, targeted, time-boxed government actions."""
    cached = _cache.get(ward_id)
    if cached and time.monotonic() - cached[0] < _CACHE_SECONDS:
        return cached[1]

    result = _recommend_actions_uncached(ward_id)
    _cache[ward_id] = (time.monotonic(), result)
    return result


def _recommend_actions_uncached(ward_id: str) -> dict:
    try:
        # 1. Fetch live metrics from data/ML modules
        aqi_data = fetch_aqi(ward_id)
        forecast_points = fetch_forecast(ward_id, 24)
        source_data = fetch_source_attribution(ward_id)
        weather_data = fetch_weather(ward_id)
        traffic_data = fetch_traffic(ward_id)
        construction_data = fetch_construction(ward_id)
    except Exception as e:
        logger.error(f"Error fetching data for ward {ward_id} recommendation: {e}", exc_info=True)
        # Return fallback mock/sensible data if core endpoints fail
        return {
            "ward_id": ward_id,
            "actions": [
                {
                    "action": "Increase road water-spraying and traffic monitoring",
                    "target": f"Ward {ward_id} main corridors",
                    "urgency": "medium",
                    "reason": f"Data ingestion issue: fallback action triggered for ward {ward_id}."
                }
            ],
            "inspection_priority": [
                {
                    "site": "Arterial road intersection",
                    "ward_id": ward_id,
                    "reason": "Visual inspection of dust/traffic levels due to API fallback",
                    "priority": 1
                }
            ]
        }

    # Prepare context block for the LLM
    context_str = f"""
Ward ID: {ward_id}
Ward Name: {aqi_data['ward_name']}

Current Air Quality (CPCB Categories: good | satisfactory | moderate | poor | very_poor | severe):
- AQI: {aqi_data['aqi']} ({aqi_data['category']})
- PM2.5: {aqi_data['pm25']} µg/m³
- PM10: {aqi_data['pm10']} µg/m³
- NO2: {aqi_data['no2']} µg/m³

Pollution Source Attribution Shares:
- Traffic share: {source_data.get('traffic', 0.0) * 100:.1f}%
- Construction share: {source_data.get('construction', 0.0) * 100:.1f}%
- Industry share: {source_data.get('industry', 0.0) * 100:.1f}%
- Dust share: {source_data.get('dust', 0.0) * 100:.1f}%
- Source Attribution Explanation: {source_data.get('reasoning', '')}

Simulated Local Activity Indicators:
- Traffic Density Index (0-1): {traffic_data.traffic_index:.2f}
- Active Construction Sites: {construction_data.active_sites} ({', '.join(construction_data.site_names) if construction_data.site_names else 'None'})

Local Weather (Delhi):
- Temperature: {weather_data.get('temp_c')} °C
- Humidity: {weather_data.get('humidity')}%
- Wind Speed: {weather_data.get('wind_kph')} kph
- Wind Direction: {weather_data.get('wind_dir')}
- Rain: {weather_data.get('rain_mm')} mm

AQI 24h Forecast:
{json.dumps(forecast_points[:6], indent=2)}
"""

    system_prompt = """You are an AI environmental advisor for the Delhi Government's environmental protection division.
Based on the current ward-level air quality, source attribution shares, local activity indicators, weather conditions, and forecast, you must recommend a set of targeted government actions and prioritize inspection sites.

Map the current situation to Delhi's regulatory levers and Graded Response Action Plan (GRAP) guidelines:
- GRAP Stage I (AQI 201-300 'Poor'): Dust control at construction sites, mechanical sweeping, road water-spraying, strict action on biomass burning.
- GRAP Stage II (AQI 301-400 'Very Poor'): Ban coal/firewood in eateries, restrict diesel generators, increase public transit frequency, dust suppression.
- GRAP Stage III (AQI 401-450 'Severe'): Ban non-essential construction/demolition, restrict BS-III petrol & BS-IV diesel vehicles.
- GRAP Stage IV (AQI >450 'Severe+'): Stop truck entry (except essentials), ban Delhi-registered diesel medium/heavy goods vehicles.

ACTION LEVERS TO RECOMMEND:
1. High traffic share: Restrict heavy diesel trucks (e.g., on Ring Road peak hours 6-10 AM), enforce PUC compliance, or promote public transit. Cite GRAP stages as appropriate.
2. High construction share: Halt open construction, mandate dust netting, enforce water spraying.
3. High dust share: Deploy road water-spraying tankers, mechanised road sweeping.
4. High industry: Audit/inspect nearby factories (e.g., Okhla Industrial Area), verify emission control, temporary shutdowns.

URGENCY RULES:
- 'high' urgency: if AQI is Poor/Very Poor/Severe (>200) and forecast trend is rising, or if a source share is extremely dominant.
- 'medium' urgency: if AQI is Moderate (101-200) or stable.
- 'low' urgency: if AQI is Good/Satisfactory (<100) or falling.

INSPECTION PRIORITY RULES:
- Propose specific sites (like 'Metro Phase-4 site', 'Okhla Industrial Area', or major roads) for inspection in this ward.
- Provide a priority rating: 1 for the most urgent/highest priority site, 2 for the second, etc.
- Base the reasons on the dominant pollution source.

You MUST respond ONLY with a valid JSON object matching this schema:
{
  "ward_id": "string (matching the input ward_id)",
  "actions": [
    {
      "action": "string (specific action description, e.g., 'Halt open construction & mandate dust netting + water spraying')",
      "target": "string (named zone, road, or factory, e.g., 'Metro Phase-4 site')",
      "urgency": "string ('high' | 'medium' | 'low')",
      "reason": "string (brief justification citing specific source attribution, forecast data, or GRAP Stage)"
    }
  ],
  "inspection_priority": [
    {
      "site": "string (name of site, e.g. 'Metro Phase-4 site' or 'Okhla Industrial Area')",
      "ward_id": "string (matching the input ward_id)",
      "reason": "string (brief reason for inspection)",
      "priority": int (priority rank: 1, 2, 3...)
    }
  ]
}

DO NOT include any markdown formatting (like ```json), notes, preamble, or trailing text. The output must be pure raw JSON."""

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the context data:\n{context_str}"}
        ]
        response = run_with_failover(lambda llm: llm.invoke(messages))
        content = response.content if hasattr(response, 'content') else str(response)
        parsed = _clean_and_parse_json(content)

        # Ensure it conforms to basic RecommendationResponse shape
        if "ward_id" not in parsed:
            parsed["ward_id"] = ward_id
        if "actions" not in parsed or not isinstance(parsed["actions"], list):
            parsed["actions"] = []
        if "inspection_priority" not in parsed or not isinstance(parsed["inspection_priority"], list):
            parsed["inspection_priority"] = []

        return parsed
    except Exception as e:
        logger.error(f"Error executing recommendation LLM for ward {ward_id}: {e}", exc_info=True)
        # Fail-safe structured response
        return {
            "ward_id": ward_id,
            "actions": [
                {
                    "action": "Restrict diesel truck movements and enforce dust control",
                    "target": "Major road corridors",
                    "urgency": "medium",
                    "reason": f"Fallback action triggered due to processing error: {str(e)}"
                }
            ],
            "inspection_priority": [
                {
                    "site": "Major ward crossroads",
                    "ward_id": ward_id,
                    "reason": "Visual survey for dust accumulation",
                    "priority": 1
                }
            ]
        }
