# TODO: Person A — fetch REAL AQI from OpenAQ (and/or CPCB), map stations→wards, write to aqi_readings.
# Called by routers/data.py and by the scheduler. Cache latest per ward in Redis.


def fetch_aqi():
    """Pull latest AQI readings for the configured city. Return list of dicts / persist to DB."""
    raise NotImplementedError("Person A: implement OpenAQ/CPCB ingestion")
