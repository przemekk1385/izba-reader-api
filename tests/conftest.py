import os
from pathlib import Path
from typing import Callable, Generator

import cv2
import numpy as np
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from faker import Faker
from httpx import AsyncClient

from izba_reader.dependencies import get_redis
from izba_reader.settings import Settings


def pytest_configure() -> None:
    fake = Faker()

    email = fake.email()
    os.environ["API_KEY"] = fake.password(length=64)
    os.environ["ORIGINS"] = "[]"
    os.environ["MAIL_FROM"] = email
    os.environ["MAIL_PASSWORD"] = fake.password()
    os.environ["MAIL_PORT"] = "587"
    os.environ["MAIL_SERVER"] = fake.domain_name()
    os.environ["MAIL_SUBJECT"] = fake.sentence()[:-1]
    os.environ["MAIL_USERNAME"] = email
    os.environ["ENVIRONMENT"] = "test"
    os.environ["SENTRY_DSN"] = "https://public@sentry.example.com/1"


@pytest_asyncio.fixture
async def async_client(settings) -> Generator[AsyncClient, None, None]:
    from izba_reader.main import app

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"X-API-KEY": settings.api_key},
    ) as ac, LifespanManager(app):
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def flush_db(settings):
    redis = get_redis(settings)
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
def settings() -> Settings:
    return Settings()
