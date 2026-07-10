# TODO: Person A — fetch REAL weather from Open-Meteo (temp, humidity, wind speed/dir) per ward centroid.
# Wind is a key feature for both forecasting (Person B) and dust attribution.


def fetch_weather(lat: float, lon: float):
    """Return current + recent-history weather for a coordinate from Open-Meteo (no API key needed)."""
    raise NotImplementedError("Person A: implement Open-Meteo ingestion")
