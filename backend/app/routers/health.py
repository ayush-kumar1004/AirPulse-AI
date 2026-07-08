# Shared liveness/readiness router. Keep dependency-free so it works even if DB/Redis are down.
from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
def health():
    return {"status": "ok", "city": settings.city, "env": settings.env}
