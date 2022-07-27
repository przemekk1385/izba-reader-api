import aioredis
from fastapi import Depends, HTTPException, status
from fastapi.params import Security
from fastapi.security import APIKeyHeader

from izba_reader.settings import Settings

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


def get_settings() -> Settings:
    return Settings()


def get_redis(settings: Settings = Depends(get_settings)):
    return aioredis.from_url(settings.redis_url, decode_responses=True)


def get_api_key(
    api_key_header: str = Security(api_key_header),
    settings: Settings = Depends(get_settings),
):
    if api_key_header == settings.api_key:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
