from redis.asyncio import Redis as AsyncRedis
import redis as sync_redis_module
from app.core.config import settings

_async_client: AsyncRedis | None = None


async def get_async_redis() -> AsyncRedis:
    global _async_client
    if _async_client is None:
        _async_client = AsyncRedis.from_url(settings.REDIS_URL, decode_responses=True)
    return _async_client


def get_sync_redis() -> sync_redis_module.Redis:
    return sync_redis_module.Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_async_redis() -> None:
    global _async_client
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None
