import json
from datetime import datetime

import aioredis
from aioredis import Redis
from fastapi import Depends

from izba_reader.config import Config, get_config


def get_redis(config: Config = Depends(get_config)):
    return aioredis.from_url(config.redis_url, decode_responses=True)


async def get_cache(key, redis: Redis = Depends(get_redis)) -> dict:
    return json.loads(await redis.get(key) or "{}")


async def set_cache(
    key: str,
    value: dict,
    config: Config = Depends(get_config),
    redis: Redis = Depends(get_redis),
) -> None:
    await redis.set(
        key,
        json.dumps(
            value, default=lambda x: x.isoformat() if isinstance(x, datetime) else x
        ),
        ex=config.ex,
    )
