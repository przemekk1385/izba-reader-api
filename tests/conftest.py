from pathlib import Path
from typing import Callable

import cv2
import numpy as np
import pytest
import pytest_asyncio
from httpx import AsyncClient

from izba_reader import app
from izba_reader.config import Config, get_config


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def image_file(faker, tmp_path) -> Callable:
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
def config_override(faker):
    app.dependency_overrides[get_config] = lambda: Config(
        redis_url=(
            f"redis://{faker.uri_path(deep=1)}:{faker.port_number(is_dynamic=True)}"
        )
    )
