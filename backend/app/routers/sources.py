# Person B — Pollution Source Detection. Owns DOCX Section 6 endpoint /api/source-attribution.
# Real logic: app.ml.source_attribution.attribute() — a transparent weighted-scoring model.
from fastapi import APIRouter, Query

from app.ml.source_attribution import attribute
from app.models.schemas import SourceBreakdown

router = APIRouter(prefix="/api", tags=["sources (Person B)"])


@router.get("/source-attribution", response_model=SourceBreakdown)
def source_attribution(ward: str = Query(..., description="ward_id")):
    """% breakdown by source + confidence + raw factors, from a transparent weighted-scoring model."""
    return SourceBreakdown(**attribute(ward))
