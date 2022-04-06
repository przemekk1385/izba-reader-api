import itertools

import pytest
from fastapi import status

from izba_reader import app, routes, timezones
from izba_reader.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def settings_override(faker):
    email = faker.email()

    app.dependency_overrides[get_settings] = lambda: Settings(
        mail_from=email,
        mail_password=faker.password(),
        mail_port=faker.port_number(is_system=True),
        mail_server=faker.domain_name(),
        mail_subject=faker.sentence(),
        mail_username=email,
    )


@pytest.mark.asyncio
async def test_ok(async_client, faker, mocked_cache, mocked_rss_services):
    mocked_service, return_value = mocked_rss_services
    all_items = list(itertools.chain(*return_value.values()))

    mocked_cache.get_cache.return_value = {
        "items": all_items,
        "time": faker.date_time_this_month(
            before_now=True, tzinfo=timezones.EUROPE_WARSAW
        ),
    }

    response = await async_client.get(routes.RSS_FEEDS)

    assert response.status_code == status.HTTP_200_OK, response.json()

    response_data = response.json()
    assert len(response_data["items"]) == len(all_items)

    mocked_cache.get_cache.assert_called_once()
    for service in mocked_service.values():
        service.assert_not_called()
    mocked_cache.set_cache.assert_not_called()


@pytest.mark.asyncio
async def test_ok_when_no_cache(async_client, mocked_cache, mocked_rss_services):
    mocked_service, return_value = mocked_rss_services
    all_items = list(itertools.chain(*return_value.values()))

    mocked_cache.get_cache.return_value = None

    response = await async_client.get(routes.RSS_FEEDS)

    assert response.status_code == status.HTTP_200_OK, response.json()

    response_data = response.json()
    assert len(response_data["items"]) == len(all_items)

    mocked_cache.get_cache.assert_called_once()
    for service in mocked_service.values():
        service.assert_called_once()
    mocked_cache.set_cache.assert_called_once()
