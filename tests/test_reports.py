import pytest
from fastapi import status

from izba_reader import routes


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_override")
async def test_send_message(async_client, faker, mocked_rollbar, mocker):
    mocker.patch(
        "izba_reader.services.mail.make_text_message",
        side_effect=Exception(faker.sentence()),
    )

    response = await async_client.get(routes.SEND_MAIL, params={"email": faker.email()})

    assert response.status_code == status.HTTP_202_ACCEPTED, response.json()

    mocked_rollbar[
        "izba_reader.decorators.rollbar"
    ].report_exc_info.assert_called_once()