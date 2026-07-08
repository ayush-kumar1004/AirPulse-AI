"""AirIntel backend — single FastAPI app. Imports every owner's router.

Shared file: change routing/CORS only by team agreement. Runs clean from commit #1 —
each router ships mock responses until its owner adds real logic.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import agents, data, forecast, health, sources

settings = get_settings()

app = FastAPI(
    title="AirIntel API",
    description="AI-Powered Urban Air Quality Intelligence — single-city prototype.",
    version="0.1.0",
)

# CORS configured ONCE here. Frontend uses exactly one backend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# One router per owner. Prefixes are the API contract — see README endpoint table.
app.include_router(health.router)                       # shared
app.include_router(data.router)                         # Person A
app.include_router(forecast.router)                     # Person B
app.include_router(sources.router)                      # Person B
app.include_router(agents.router)                       # Person C


@app.get("/")
def root():
    return {"app": "AirIntel", "city": settings.city, "docs": "/docs"}
