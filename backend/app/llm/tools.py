# TODO: Person C — LangChain tools that wrap the OTHER modules so agents can call them.
# These call Person A's and Person B's functions IN-PROCESS (no HTTP). Import their modules directly.
#   get_aqi(ward_id)        -> from app.data_ingestion / routers.data logic
#   get_forecast(ward_id)   -> from app.ml.forecast_model
#   get_sources(ward_id)    -> from app.ml.source_attribution
#   get_weather(ward_id)    -> from app.data_ingestion.weather_ingest
# Wrap each with @tool and give a clear docstring — the officer chat agent picks tools by description.


def build_tools():
    """Return the list of LangChain tools for the officer chat agent. TODO: Person C."""
    raise NotImplementedError("Person C: expose module functions as @tool")
