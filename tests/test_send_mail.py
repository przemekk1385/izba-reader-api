import pytest
from fastapi import status
from fastapi_mail import FastMail

from izba_reader import routes


@pytest.mark.asyncio
@pytest.mark.usefixtures("mocked_html_services", "mocked_rss_services")
async def test_ok(async_client, faker, mocked_cache, mocked_rollbar, mocker):
    email = faker.email()

    mocked_cache.get_cache.return_value = None
    mocked_send_message = mocker.patch.object(FastMail, "send_message")

    response = await async_client.get(routes.SEND_MAIL, params={"email": email})

    assert response.status_code == status.HTTP_202_ACCEPTED, response.json()

    assert email in mocked_send_message.call_args[0][0].recipients

    assert mocked_cache.get_cache.call_count == mocked_cache.set_cache.call_count == 2

    mocked_rollbar[
        "izba_reader.services.mail.rollbar"
    ].report_message.assert_called_once()
