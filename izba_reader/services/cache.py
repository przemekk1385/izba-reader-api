import json
from datetime import datetime

import aioredis
from aioredis import Redis
from fastapi import Depends

from izba_reader.settings import Settings, get_settings


def get_redis(settings: Settings = Depends(get_settings)):
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def get_cache(key, redis: Redis = Depends(get_redis)) -> dict:
    return json.loads(await redis.get(key) or "{}")


async def set_cache(
    key: str,
    value: dict,
    settings: Settings = Depends(get_settings),
    redis: Redis = Depends(get_redis),
) -> None:
    await redis.set(
        key,
        json.dumps(
            value, default=lambda x: x.isoformat() if isinstance(x, datetime) else x
        ),
        ex=settings.ex,
    )
