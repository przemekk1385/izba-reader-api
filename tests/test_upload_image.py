import pytest
from fastapi import status
from httpx import AsyncClient

from izba_reader import app, routes


@pytest.mark.anyio
async def test_ok(image_file):
    path = image_file(3, 4)

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

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
    assert "text/x-python" in response.json()["detail"]


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

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
    assert "4:3" in response.json()["detail"]
