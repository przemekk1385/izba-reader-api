import cv2
import pytest
from fastapi import status

from izba_reader import constants, routes


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_override")
async def test_ok(async_client, image_file):
    path = image_file(3000, 4000)

    with open(path, "rb") as img:
        response = await async_client.post(
            routes.HEADER_LIST,
            files={
                "uploaded_file": (
                    img.name,
                    img,
                    # "image/jpeg"
                )
            },
        )

    assert response.status_code == status.HTTP_200_OK, response.json()

    response_data = response.json()
    assert response_data["size"]
    assert response_data["uuid"]

    img = cv2.imread(str(constants.MEDIA_ROOT / f"{response_data['uuid']}.jpg"), 0)
    assert img.shape == (750, 1000)


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_override")
async def test_invalid_mime_type(async_client):
    with open(__file__, "rb") as f:
        response = await async_client.post(
            routes.HEADER_LIST,
            files={
                "uploaded_file": (
                    f.name,
                    f,
                )
            },
        )

    assert (
        response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    ), response.json()

    response_data = response.json()
    assert "text/x-python" in response_data["detail"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_override")
async def test_invalid_aspect_ratio(async_client, image_file):
    path = image_file(1000, 2000)

    with open(path, "rb") as img:
        response = await async_client.post(
            routes.HEADER_LIST,
            files={
                "uploaded_file": (
                    img.name,
                    img,
                    # "image/jpeg"
                )
            },
        )

    assert (
        response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    ), response.json()

    response_data = response.json()
    assert "4:3" in response_data["detail"]
