"""AirPulse AI backend — single FastAPI app. Imports every owner's router.

Shared file: change routing/CORS only by team agreement. Runs clean from commit #1 —
each router ships mock responses until its owner adds real logic.
"""
import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.data_ingestion.aqi_refresh import aqi_refresh_loop
from app.database import AsyncSessionLocal
from app.routers import agents, data, forecast, health, sources
from app.startup import bootstrap_database

settings = get_settings()

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

# Suppress benign advisory logs from google-genai AFC deprecation notice
logging.getLogger("google_genai.models").setLevel(logging.ERROR)


# How often to re-pull city AQI. Open-Meteo updates hourly, so anything faster
# just burns requests.
AQI_REFRESH_SECONDS = 30 * 60


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the schema and seed wards/industrial zones/AQI so a fresh
    # `docker compose up` works with no manual script runs. Idempotent.
    await bootstrap_database()

    # Keep AQI current for the whole city while the app runs.
    refresher = asyncio.create_task(
        aqi_refresh_loop(AQI_REFRESH_SECONDS, AsyncSessionLocal)
    )
    try:
        yield
    finally:
        refresher.cancel()
        with suppress(asyncio.CancelledError):
            await refresher


app = FastAPI(
    title="AirPulse AI API",
    description="AI-Powered Urban Air Quality Intelligence — single-city prototype.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configured for local dev and cloud deployments (*.onrender.com, *.vercel.app)
cors_origins = [settings.frontend_origin, "http://localhost:5173"]
if settings.frontend_origin and settings.frontend_origin not in cors_origins:
    cors_origins.append(settings.frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.onrender\.com|https://.*\.vercel\.app|http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_ORIGINS = cors_origins


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return a real 500 body with CORS headers instead of a bare connection drop."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)

    origin = request.headers.get("origin")
    headers = {"Access-Control-Allow-Origin": origin} if origin else {}

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
        headers=headers,
    )

# One router per owner. Prefixes are the API contract — see README endpoint table.
app.include_router(health.router)                       # shared
app.include_router(data.router, prefix="/api")          # Person A
app.include_router(forecast.router)                     # Person B
app.include_router(sources.router)                      # Person B
app.include_router(agents.router)                       # Person C


@app.get("/")
def root():
    return {"app": "AirPulse AI", "city": settings.city, "docs": "/docs"}
