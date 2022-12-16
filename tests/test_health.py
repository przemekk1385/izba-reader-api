import pytest
from starlette import status

from izba_reader.main import routes


@pytest.fixture
def break_redis(faker, settings):
    from izba_reader.dependencies import get_settings
    from izba_reader.main import app

    redis_url = settings.redis_url
    settings.redis_url = "redis://non-existing-host:9999"

    app.dependency_overrides[get_settings] = lambda: settings
    yield

    settings.redis_url = redis_url


@pytest.mark.asyncio
async def test_ok(async_client):
    response = await async_client.get(routes.HEALTH_LIST)

    assert response.status_code == status.HTTP_200_OK, response.json()


@pytest.mark.asyncio
@pytest.mark.usefixtures("break_redis")
async def test_failed_no_redis(async_client):
    response = await async_client.get(routes.HEALTH_LIST)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, response.json()
