import pytest
from faker import Faker
from fastapi import status
from fastapi_mail import FastMail
from pydantic import HttpUrl

from izba_reader import routes, timezones

fake = Faker()


async def mocked_fetch_html(urls: list[HttpUrl]) -> dict[HttpUrl, str]:
    return {
        url: [
            {
                "link": fake.uri(),
                "description": fake.paragraph(),
                "title": fake.sentence(),
                "date": fake.date_time_this_month(
                    before_now=True, tzinfo=timezones.EUROPE_WARSAW
                ),
            }
            for _ in range(fake.random_int(min=2, max=10))
        ]
        for url in urls
    }


async def mocked_fetch_rss(urls: list[HttpUrl]) -> dict[HttpUrl, str]:
    return {
        url: [
            {
                "title": fake.sentence(),
                "description": fake.paragraph(),
                "link": fake.uri(),
            }
            for _ in range(fake.random_int(min=2, max=10))
        ]
        for url in urls
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_override")
async def test_ok(async_client, faker, mocked_rollbar, mocker):
    email = faker.email()

    mocker.patch("izba_reader.services.fetch.html", new=mocked_fetch_html)
    mocker.patch("izba_reader.services.fetch.rss", new=mocked_fetch_rss)

    mocked_send_message = mocker.patch.object(FastMail, "send_message")

    response = await async_client.get(routes.MAIL_SEND, params={"email": email})

    assert response.status_code == status.HTTP_202_ACCEPTED, response.json()

    assert email in mocked_send_message.call_args[0][0].recipients

    mocked_rollbar[
        "izba_reader.services.mail.rollbar"
    ].report_message.assert_called_once()
