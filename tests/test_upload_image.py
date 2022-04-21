import cv2
import pytest
from fastapi import status

from izba_reader import constants, routes
from izba_reader.enums import UploadImagesError


@pytest.mark.asyncio
@pytest.mark.usefixtures("cleanup_test_media_files", "mark_test_media_files")
async def test_ok(async_client, image_file, mocked_rollbar):
    with open(image_file(3000, 4000), "rb") as img1, open(
        image_file(3000, 4000), "rb"
    ) as img2:
        response = await async_client.post(
            routes.UPLOAD_IMAGE,
            files=[
                (
                    "uploaded_images",
                    (
                        img1.name,
                        img1,
                        # "image/jpeg"
                    ),
                ),
                (
                    "uploaded_images",
                    (
                        img2.name,
                        img2,
                        # "image/jpeg"
                    ),
                ),
            ],
        )

    assert response.status_code == status.HTTP_200_OK, response.json()

    response_data = response.json()
    assert len(response_data) == 2
    assert all("url" in item for item in response_data)

    for item in response_data:
        img = cv2.imread(str(constants.MEDIA_ROOT / item["url"].split("/")[-1]), 0)
        assert img.shape == (750, 1000)

    assert mocked_rollbar["izba_reader.main.rollbar"].report_message.call_count == 2


@pytest.mark.asyncio
async def test_invalid_mime_type(async_client):
    with open(__file__, "rb") as f:
        response = await async_client.post(
            routes.UPLOAD_IMAGE,
            files={
                "uploaded_images": (
                    f.name,
                    f,
                )
            },
        )

    assert response.status_code == status.HTTP_200_OK, response.json()

    response_data = response.json()
    assert response_data[0]["error"] == UploadImagesError.UNHANDLED_MIME_TYPE.value


@pytest.mark.asyncio
async def test_invalid_aspect_ratio(async_client, image_file):
    path = image_file(1000, 2000)

    with open(path, "rb") as img:
        response = await async_client.post(
            routes.UPLOAD_IMAGE,
            files={
                "uploaded_images": (
                    img.name,
                    img,
                    # "image/jpeg"
                )
            },
        )

    assert response.status_code == status.HTTP_200_OK, response.json()

    response_data = response.json()
    assert response_data[0]["error"] == UploadImagesError.INVALID_ASPECT_RATIO.value
