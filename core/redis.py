import asyncio

from redis.asyncio import from_url, Redis

from setting import setting

redis: Redis | None = None

if setting.redis_url is not None:
    redis = from_url('redis://' + setting.redis_url, encoding="utf-8", decode_responses=True)


async def clear_cache_by_namespace(namespace: str):
    keys = await redis.keys(f'{namespace}:*')
    # parallel delete
    await asyncio.gather(*[redis.delete(key) for key in keys])
