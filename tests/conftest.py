from pathlib import Path
from typing import Callable

import cv2
import numpy as np
import pytest


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

        cv2.imwrite(path.as_posix(), img)

        return path

    yield make_image_file
