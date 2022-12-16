import pytest
from starlette import status

from izba_reader import routes


@pytest.mark.asyncio
async def test_ok(async_client):
    response = await async_client.get(routes.ARTICLE_LIST)

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert len(response.json())
