# TODO: Person A — Redis client + cache helpers (get/set JSON with TTL) for AQI + forecast caching.
import json
from typing import Any, Optional

import redis

from app.config import get_settings

settings = get_settings()

# decode_responses=True so we get str back, not bytes.
client = redis.from_url(settings.redis_url, decode_responses=True)


def cache_get(key: str) -> Optional[Any]:
    raw = client.get(key)
    return json.loads(raw) if raw else None


def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
