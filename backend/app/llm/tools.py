# LangChain tools wrapping in-process functions, via the data_bridge sync layer.
from langchain_core.tools import tool

from app.llm.data_bridge import fetch_aqi, fetch_forecast, fetch_source_attribution, fetch_weather
from app.llm.recommendation_agent import recommend_actions


@tool
def get_aqi(ward_id: str) -> str:
    """Get the current AQI and pollutant breakdown (PM2.5, PM10, NO2) for a specific Delhi ward.
    Use this to answer questions about the current air pollution levels in a ward.
    """
    try:
        res = fetch_aqi(ward_id)
        return (f"Ward: {res['ward_name']} ({res['ward_id']}), AQI: {res['aqi']}, Category: {res['category']}, "
                f"PM2.5: {res['pm25']} ug/m3, PM10: {res['pm10']} ug/m3, NO2: {res['no2']} ug/m3, "
                f"updated at {res['updated_at']}")
    except Exception as e:
        return f"Error getting AQI for ward {ward_id}: {str(e)}"


@tool
def get_predict(ward_id: str) -> str:
    """Get the AQI prediction forecast for the next 24 hours in a specific Delhi ward.
    Use this to explain how the air quality is expected to change tomorrow or in the future.
    """
    try:
        points = fetch_forecast(ward_id, 24)
        lines = []
        for p in points[:8]:  # Show first few hours of forecast
            lines.append(f"{p['timestamp']}: Predicted AQI: {p['predicted_aqi']} (Trend: {p['trend']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error getting forecast for ward {ward_id}: {str(e)}"


@tool
def get_source_attribution(ward_id: str) -> str:
    """Get the percentage breakdown of pollution sources (traffic, construction, industry, dust) for a specific Delhi ward.
    Use this to answer questions like 'Why is this ward polluted?' or to explain the dominant pollution driver.
    """
    try:
        res = fetch_source_attribution(ward_id)
        shares = f"Traffic: {res['traffic']*100:.1f}%, Construction: {res['construction']*100:.1f}%, Industry: {res['industry']*100:.1f}%, Dust: {res['dust']*100:.1f}%"
        return f"Source Attribution for ward {ward_id}: {shares}. Reason: {res['reasoning']}. Confidence: {res['confidence'] * 100:.0f}%"
    except Exception as e:
        return f"Error getting source attribution for ward {ward_id}: {str(e)}"


@tool
def get_weather(ward_id: str) -> str:
    """Get current weather conditions (temperature, humidity, wind speed, wind direction, rain) for a specific Delhi ward.
    Use this to explain how weather conditions (like wind speed, wind direction or rain) affect pollution.
    """
    try:
        res = fetch_weather(ward_id)
        return (f"Weather for ward {ward_id}: Temp: {res.get('temp_c')} C, "
                f"Wind: {res.get('wind_kph')} kph from {res.get('wind_dir')}, "
                f"Humidity: {res.get('humidity')}%, Rain: {res.get('rain_mm')} mm")
    except Exception as e:
        return f"Error getting weather for ward {ward_id}: {str(e)}"


@tool
def get_recommendations(ward_id: str) -> str:
    """Get recommended government actions and site inspection priority lists for a specific Delhi ward.
    Use this to answer questions about what the government is doing or should do to combat pollution.
    """
    try:
        res = recommend_actions(ward_id)
        actions = []
        for idx, act in enumerate(res.get("actions", [])):
            actions.append(f"{idx+1}. Urgency: {act['urgency'].upper()} | Action: {act['action']} on {act['target']} because: {act['reason']}")

        inspections = []
        for ins in res.get("inspection_priority", []):
            inspections.append(f"Inspection #{ins['priority']}: {ins['site']} in ward {ins['ward_id']} - Reason: {ins['reason']}")

        return "Recommendations:\n" + "\n".join(actions) + "\n\nInspection Priorities:\n" + "\n".join(inspections)
    except Exception as e:
        return f"Error getting recommendations for ward {ward_id}: {str(e)}"


def build_tools():
    """Return the list of LangChain tools for the officer chat agent."""
    return [get_aqi, get_predict, get_source_attribution, get_weather, get_recommendations]
