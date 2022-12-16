import aioredis
from fastapi import Depends, HTTPException, status
from fastapi.params import Security
from fastapi.security import APIKeyHeader
from pydantic import ValidationError

from izba_reader.decorators import capture_exception
from izba_reader.settings import Settings

_api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


@capture_exception
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError:
        # The "dev" Doppler configuration defines environment variables with the "APP_"
        # prefix, which is omitted when the application is running in a Docker
        # container. The following class guarantees that variables are fetched correctly
        # when the application is running without Docker.
        class DopplerDevSettings(Settings):
            class Config:
                env_prefix = "app_"

        return DopplerDevSettings()


def get_redis(settings: Settings = Depends(get_settings)):
    return aioredis.from_url(settings.redis_url, decode_responses=True)


def get_api_key(
    api_key_header: str = Security(_api_key_header),
    settings: Settings = Depends(get_settings),
):
    if api_key_header == settings.api_key:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
