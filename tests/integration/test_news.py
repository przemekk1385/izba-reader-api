from datetime import date, timedelta

import pytest
from starlette import status

from izba_reader import routes
from izba_reader.constants import NEWS_URLS


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_override")
async def test_ok(async_client):
    response = await async_client.get(
        routes.NEWS_LIST,
        params={"dt": date.today() + timedelta(days=1), "urls": NEWS_URLS},
    )

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert not len(response.json())

    dt = date.today()
    attempt = 1
    while True:
        response = await async_client.get(
            routes.NEWS_LIST, params={"dt": dt, "urls": NEWS_URLS}
        )

        assert response.status_code == status.HTTP_200_OK, response.json()

        if len(response.json()):
            break
        else:
            dt -= timedelta(days=1)
            attempt += 1

        if attempt == 7:
            assert False, "Too many attempts"
