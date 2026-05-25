import orjson
from typing import Any
from app.shared.redis_client import get_cache_redis

CACHE_TTL = 30


async def cache_get(key: str) -> bytes | None:
    redis = await get_cache_redis()
    return await redis.get(key)


async def cache_set(key: str, value: bytes, ttl: int = CACHE_TTL) -> None:
    redis = await get_cache_redis()
    await redis.setex(key, ttl, value)


async def cache_delete(*keys: str) -> None:
    if not keys:
        return
    redis = await get_cache_redis()
    await redis.delete(*keys)


def serialize(data: Any) -> bytes:
    return orjson.dumps(data)
