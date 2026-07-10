import redis.asyncio as redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global Redis client instance
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def check_redis_connection():
    try:
        await redis_client.ping()
        logger.info("Successfully connected to Redis.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise e
