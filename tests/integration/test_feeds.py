import pytest
from starlette import status

from izba_reader import routes
from izba_reader.constants import FEED_URLS


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_override")
async def test_ok(async_client):
    response = await async_client.get(routes.FEED_LIST, params={"urls": FEED_URLS})

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json())
