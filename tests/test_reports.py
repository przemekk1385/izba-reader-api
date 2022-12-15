from smtplib import SMTP

import pytest
from fastapi import status

from izba_reader import routes


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_override")
async def test_send_mail(async_client, faker, mocked_rollbar, mocker):
    mocked_send_message = mocker.patch.object(SMTP, "send_message")
    mocked_send_message.side_effect = Exception(faker.sentence())

    with pytest.raises(Exception):
        response = await async_client.get(
            routes.MAIL_SEND, params={"email": faker.email()}
        )

        assert response.status_code == status.HTTP_202_ACCEPTED, response.json()

        mocked_rollbar[
            "izba_reader.decorators.rollbar"
        ].report_exc_info.assert_called_once()
