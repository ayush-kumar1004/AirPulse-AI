import redis.asyncio as redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global Redis client instance with short socket timeouts so offline Redis never hangs endpoints
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=1.0,
    socket_timeout=1.0,
)

async def check_redis_connection():
    try:
        await redis_client.ping()
        logger.info("Successfully connected to Redis.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise e
