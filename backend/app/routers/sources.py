# Person B — Pollution Source Detection. Owns DOCX Section 6 endpoint /api/source-attribution.
# Real logic: app.ml.source_attribution.attribute() — a transparent weighted-scoring model.
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.ml.source_attribution import attribute
from app.models.schemas import SourceBreakdown

router = APIRouter(prefix="/api", tags=["sources (Person B)"])


@router.get("/source-attribution", response_model=SourceBreakdown)
async def source_attribution(ward_id: str = Query(...), session: AsyncSession = Depends(get_db)):
    """% breakdown by source + confidence + raw factors, from a transparent weighted-scoring model."""
    result = await attribute(session, ward_id)
    return SourceBreakdown(**result)
