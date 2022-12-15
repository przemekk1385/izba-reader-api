from pathlib import Path
from typing import Callable, Generator

import cv2
import numpy as np
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from izba_reader import app
from izba_reader.dependencies import get_redis, get_settings
from izba_reader.settings import Settings


@pytest_asyncio.fixture
async def async_client(settings_override) -> Generator[AsyncClient, None, None]:
    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"X-API-KEY": settings_override.api_key},
    ) as ac, LifespanManager(app):
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def flush_db(settings_override):
    redis = get_redis(settings_override)
    await redis.flushdb()


@pytest.fixture
def image_file(faker, tmp_path) -> Callable[[int, int], Path]:
    def make_image_file(height: int = 1, width: int = 1) -> Path:
        path = tmp_path / f"{faker.uuid4()}.jpg"

        img = np.zeros((height, width, 3), np.uint8)
        img[:, :] = (
            faker.random_int(0, 255),
            faker.random_int(0, 255),
            faker.random_int(0, 255),
        )

        cv2.imwrite(str(path), img)

        return path

    return make_image_file


@pytest.fixture
def settings_override(faker, mocker) -> Settings:
    email = faker.email()
    settings = Settings(
        api_key=faker.password(length=64),
        origins=["http://test"],
        mail_from=email,
        mail_password=faker.password(),
        mail_port=587,
        mail_server=faker.domain_name(),
        mail_subject=faker.sentence()[:-1],
        mail_username=email,
        environment="test",
        sentry_dsn="https://public@sentry.example.com/1",
    )

    app.dependency_overrides[get_settings] = lambda: settings
    mocker.patch("izba_reader.main.get_settings", return_value=settings)
    mocker.patch("izba_reader.services.fetch.get_settings", return_value=settings)
    mocker.patch("izba_reader.services.mail.get_settings", return_value=settings)

    return settings
