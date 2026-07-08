# TODO: Person B — Pollution Source Detection. Owns DOCX Section 6 endpoint /api/source-attribution.
# Transparent weighted-scoring (NOT a black box). Returns MOCK now; swap for app.ml.source_attribution.attribute().
from fastapi import APIRouter, Query

from app.models.schemas import SourceBreakdown

router = APIRouter(prefix="/api", tags=["sources (Person B)"])


@router.get("/source-attribution", response_model=SourceBreakdown)
def source_attribution(ward: str = Query(..., description="ward_id")):
    """% breakdown by source + confidence + raw factors. TODO: Person B — weighted-scoring using
    traffic %, construction activity, industrial proximity, wind direction, dust conditions."""
    return SourceBreakdown(
        ward_id=ward,
        traffic=0.45,
        construction=0.25,
        industry=0.20,
        dust=0.10,
        confidence=0.78,
        raw_factors={"traffic_index": 0.72, "construction_sites": 2, "industry_proximity_km": 3.1,
                     "wind_dir": "NW", "wind_kph": 8.0},
        reasoning="Traffic dominant due to rush-hour congestion; construction elevated by two active sites; "
                  "low NW wind keeps local sources trapped, so dust contribution stays modest.",
    )
