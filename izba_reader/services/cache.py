import json
from datetime import datetime

import aioredis

from izba_reader.config import config

redis = aioredis.from_url(config.redis_url, decode_responses=True)


async def get_cache(key) -> dict:
    return json.loads(await redis.get(key) or "{}")


async def set_cache(key: str, value: dict) -> None:
    await redis.set(
        key,
        json.dumps(
            value, default=lambda x: x.isoformat() if isinstance(x, datetime) else x
        ),
        ex=config.ex,
    )
