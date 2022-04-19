from functools import lru_cache

import aioredis
from fastapi import Depends

from izba_reader.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_redis(settings: Settings = Depends(get_settings)):
    return aioredis.from_url(settings.redis_url, decode_responses=True)
