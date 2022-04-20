import os
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Generator
from unittest.mock import Mock

import cv2
import numpy as np
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from izba_reader import constants, timezones
from izba_reader.services import html, rss


@pytest_asyncio.fixture
async def async_client(app) -> Generator[AsyncClient, None, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac, LifespanManager(app):
        yield ac


@pytest.fixture
def app(faker, mocker):
    email = faker.email()

    mocker.patch.dict(
        os.environ,
        {
            "MAIL_FROM": email,
            "MAIL_PASSWORD": faker.password(),
            "MAIL_PORT": str(faker.port_number(is_system=True)),
            "MAIL_SERVER": faker.domain_name(),
            "MAIL_SUBJECT": faker.sentence(),
            "MAIL_USERNAME": email,
            "ENVIRONMENT": "test",
            "ROLLBAR_ACCESS_TOKEN": faker.password(),
            "CORS_ALLOW_ORIGINS": '["http://test"]',
        },
    )

    from izba_reader.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
def cleanup_test_media_files():
    yield
    for path in constants.MEDIA_ROOT.glob("**/test_*"):
        path.unlink()


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
def mark_test_media_files(app, faker, mocker):
    mocker.patch("izba_reader.main.uuid4", return_value=f"test_{faker.uuid4()}")


@pytest.fixture(autouse=True)
def mocked_cache(mocker) -> SimpleNamespace:
    return SimpleNamespace(
        get_cache=mocker.patch("izba_reader.tasks.get_cache"),
        set_cache=mocker.patch("izba_reader.tasks.set_cache"),
    )


@pytest.fixture
def mocked_html_services(faker, mocker) -> tuple[dict, dict]:
    return_value = {
        name: [
            {
                "link": faker.uri(),
                "description": faker.paragraph(),
                "title": faker.sentence(),
                "date": faker.date_time_this_month(
                    before_now=True, tzinfo=timezones.EUROPE_WARSAW
                ),
            }
            for _ in range(faker.random_int(min=2, max=10))
        ]
        for name in html.__all__
    }

    mocked_service = {
        name: mocker.patch(f"izba_reader.services.html.{name}", return_value=value)
        for name, value in return_value.items()
    }

    return mocked_service, return_value


@pytest.fixture
def mocked_rollbar(mocker) -> dict[str, Mock]:
    return {
        module: mocker.patch(module, return_value=Mock())
        for module in (
            "izba_reader.main.rollbar",
            "izba_reader.tasks.rollbar",
            "izba_reader.services.mail.rollbar",
        )
    }


@pytest.fixture
def mocked_rss_services(faker, mocker) -> tuple[dict, dict]:
    return_value = {
        name: [
            {
                "title": faker.sentence(),
                "description": faker.paragraph(),
                "link": faker.uri(),
            }
            for _ in range(faker.random_int(min=2, max=10))
        ]
        for name in rss.__all__
    }

    mocked_service = {
        name: mocker.patch(f"izba_reader.services.rss.{name}", return_value=value)
        for name, value in return_value.items()
    }

    return mocked_service, return_value
