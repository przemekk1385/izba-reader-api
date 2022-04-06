import itertools

import pytest
from fastapi import status

from izba_reader import routes, timezones


@pytest.mark.asyncio
@pytest.mark.usefixtures("mail_settings_override")
async def test_ok(async_client, faker, mocked_cache, mocked_html_services):
    mocked_service, return_value = mocked_html_services
    all_items = list(itertools.chain(*return_value.values()))

    mocked_cache.get_cache.return_value = {
        "items": all_items,
        "time": faker.date_time_this_month(
            before_now=True, tzinfo=timezones.EUROPE_WARSAW
        ),
    }

    response = await async_client.get(routes.WEB_SCRAPERS)

    assert response.status_code == status.HTTP_200_OK, response.json()

    response_data = response.json()
    assert len(response_data["items"]) == len(all_items)

    mocked_cache.get_cache.assert_called_once()
    for service in mocked_service.values():
        service.assert_not_called()
    mocked_cache.set_cache.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.usefixtures("mail_settings_override")
async def test_ok_when_no_cache(async_client, mocked_cache, mocked_html_services):
    mocked_service, return_value = mocked_html_services
    all_items = list(itertools.chain(*return_value.values()))

    mocked_cache.get_cache.return_value = None

    response = await async_client.get(routes.WEB_SCRAPERS)

    assert response.status_code == status.HTTP_200_OK, response.json()

    response_data = response.json()
    assert len(response_data["items"]) == len(all_items)

    mocked_cache.get_cache.assert_called_once()
    for service in mocked_service.values():
        service.assert_called_once()
    mocked_cache.set_cache.assert_called_once()
