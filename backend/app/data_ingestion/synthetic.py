# TODO: Person A — SIMULATED traffic/construction/industry signals, rules-based & realistic.
# Stated openly in demo as simulated. Deterministic per (ward, hour) so demo is reproducible.
# Suggested rules:
#   traffic_index: peaks 08-10 & 18-20 on weekdays, lower weekends; scaled by ward "road density".
#   construction_active: fixed set of "construction ward-ids", on during daytime.
#   industry_load: constant-ish per ward from an "industrial zone" flag + small noise.


def synthetic_signals(ward_id: str, hour: int, weekday: bool = True) -> dict:
    """Return {'traffic_index', 'construction_active', 'industry_load'} for a ward/hour."""
    raise NotImplementedError("Person A: implement rules-based synthetic generator")
