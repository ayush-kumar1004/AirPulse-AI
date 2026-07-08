# TODO: Person B — TRANSPARENT weighted-scoring source attribution (NOT a black-box classifier).
# Combine: traffic_index, construction_active, industry_load (Person A synthetic) + weather
# (low wind -> dust/stagnation) + AQI composition (PM2.5 vs PM10 ratio).
# Output normalised shares that sum to 1 + a confidence score + a human explanation.
# Called by routers/sources.py — MUST match schemas.SourceBreakdown.

# Suggested starting weights (tune during the build):
WEIGHTS = {"traffic": 0.40, "construction": 0.25, "industry": 0.20, "dust": 0.15}


def attribute(ward_id: str) -> dict:
    """Return {'traffic','construction','industry','dust','confidence','explanation'}."""
    raise NotImplementedError("Person B: implement weighted-scoring attribution")
