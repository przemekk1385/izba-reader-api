import pytest
from starlette import status

from izba_reader import app, routes
from izba_reader.settings import Settings, get_settings


@pytest.fixture
def settings_override(faker):
    app.dependency_overrides[get_settings] = lambda: Settings(
        redis_url=(
            f"redis://{faker.uri_path(deep=1)}:{faker.port_number(is_dynamic=True)}"
        ),
    )


@pytest.mark.asyncio
async def test_ok(async_client):
    response = await async_client.get(routes.HEALTH)

    assert response.status_code == status.HTTP_200_OK, response.json()


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_override")
async def test_failed_no_redis(async_client):
    response = await async_client.get(routes.HEALTH)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, response.json()
