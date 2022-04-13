import pytest
from starlette import status

from izba_reader import app, routes
from izba_reader.dependencies import get_settings


@pytest.fixture
def break_redis(faker, settings_override):
    settings_override.redis_url = (
        f"redis://{faker.uri_path(deep=1)}:{faker.port_number(is_dynamic=True)}"
    )

    app.dependency_overrides[get_settings] = lambda: settings_override


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_override")
async def test_ok(async_client, mocked_rollbar):
    response = await async_client.get(routes.HEALTH)

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert mocked_rollbar["izba_reader.main.rollbar"].report_message.call_count == 2


@pytest.mark.asyncio
@pytest.mark.usefixtures("break_redis")
async def test_failed_no_redis(async_client, mocked_rollbar):
    response = await async_client.get(routes.HEALTH)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, response.json()
    mocked_rollbar["izba_reader.main.rollbar"].report_message.assert_called_once()
