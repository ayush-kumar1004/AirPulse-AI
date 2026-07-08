# TODO: Person C — Citizen Health Advisor agent. Multilingual (English + Hindi + one regional language).
# Personalise on user profile (asthma, jogger, elderly, child) + ward AQI + forecast.
# MUST match schemas.CitizenAdviceResponse. Return advice in the requested `language`.


def advise(ward_id: str, language: str = "en", profile: str | None = None) -> dict:
    """Return {'ward_id','language','advice','aqi'} — personalised health guidance."""
    raise NotImplementedError("Person C: implement citizen advisor (Claude, multilingual)")
