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

from izba_reader import app, timezones
from izba_reader.dependencies import get_settings
from izba_reader.services import html, rss
from izba_reader.settings import Settings


@pytest.fixture(scope="session", autouse=True)
def session_mocked_rollbar(session_mocker) -> dict[str, Mock]:
    return {
        module: session_mocker.patch(module, return_value=Mock())
        for module in (
            "izba_reader.main.rollbar",
            "izba_reader.tasks.rollbar",
            "izba_reader.services.mail.rollbar",
        )
    }


@pytest_asyncio.fixture
async def async_client() -> Generator[AsyncClient, None, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac, LifespanManager(app):
        yield ac


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
def mocked_rollbar(session_mocked_rollbar) -> Generator[dict[str, Mock], None, None]:
    yield session_mocked_rollbar
    for mocked_rollbar in session_mocked_rollbar.values():
        mocked_rollbar.report_message.reset_mock()


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


@pytest.fixture
def settings_override(faker, mocker) -> Settings:
    email = faker.email()
    settings = Settings(
        mail_from=email,
        mail_password=faker.password(),
        mail_port=faker.port_number(is_system=True),
        mail_server=faker.domain_name(),
        mail_subject=faker.sentence(),
        mail_username=email,
        environment="test",
        rollbar_access_token=faker.password(),
    )

    app.dependency_overrides[get_settings] = lambda: settings
    mocker.patch("izba_reader.main.get_settings", return_value=settings)

    return settings
