import pytest
from starlette import status

from izba_reader import routes


@pytest.mark.asyncio
async def test_ok(async_client):
    response = await async_client.get(routes.HEALTH)

    assert response.status_code == status.HTTP_200_OK, response.json()


@pytest.mark.asyncio
@pytest.mark.usefixtures("config_override")
async def test_failed_no_redis(async_client):
    response = await async_client.get(routes.HEALTH)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, response.json()
