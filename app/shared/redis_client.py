from redis.asyncio import Redis as AsyncRedis
import redis as sync_redis_module
from app.core.config import settings

_async_client: AsyncRedis | None = None
_cache_client: AsyncRedis | None = None


async def get_async_redis() -> AsyncRedis:
    global _async_client
    if _async_client is None:
        _async_client = AsyncRedis.from_url(
            settings.REDIS_URL, decode_responses=True, max_connections=5
        )
    return _async_client


async def get_cache_redis() -> AsyncRedis:
    """Cliente Redis com decode_responses=False para armazenar bytes JSON cacheados."""
    global _cache_client
    if _cache_client is None:
        _cache_client = AsyncRedis.from_url(
            settings.REDIS_URL, decode_responses=False, max_connections=5
        )
    return _cache_client


def get_sync_redis() -> sync_redis_module.Redis:
    return sync_redis_module.Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_async_redis() -> None:
    global _async_client, _cache_client
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None
    if _cache_client is not None:
        await _cache_client.aclose()
        _cache_client = None
