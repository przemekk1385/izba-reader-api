import cv2
import pytest
from fastapi import status
from httpx import AsyncClient

from izba_reader import app, routes
from izba_reader.constants import IMAGES_DIR


@pytest.mark.anyio
async def test_ok(image_file):
    path = image_file(3000, 4000)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        with open(path, "rb") as image_file:
            response = await ac.post(
                routes.UPLOAD_IMAGE,
                files={
                    "uploaded_file": (
                        image_file.name,
                        image_file,
                        # "image/jpeg"
                    )
                },
            )

    assert response.status_code == status.HTTP_200_OK, response.json()

    response_data = response.json()
    assert response_data["filename"]

    img = cv2.imread(str(IMAGES_DIR / response_data["filename"]), 0)
    assert img.shape == (750, 1000)


@pytest.mark.anyio
async def test_invalid_mime_type():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        with open(__file__, "rb") as image_file:
            response = await ac.post(
                routes.UPLOAD_IMAGE,
                files={
                    "uploaded_file": (
                        image_file.name,
                        image_file,
                        # "image/jpeg"
                    )
                },
            )

    assert (
        response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    ), response.json()

    response_data = response.json()
    assert "text/x-python" in response_data["detail"]


@pytest.mark.anyio
async def test_invalid_aspect_ratio(image_file):
    path = image_file()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        with open(path, "rb") as image_file:
            response = await ac.post(
                routes.UPLOAD_IMAGE,
                files={
                    "uploaded_file": (
                        image_file.name,
                        image_file,
                        # "image/jpeg"
                    )
                },
            )

    assert (
        response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    ), response.json()

    response_data = response.json()
    assert "4:3" in response_data["detail"]
