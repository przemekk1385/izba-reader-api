from datetime import datetime, timedelta
from typing import Callable
from unittest.mock import Mock

import pytest
from faker import Faker
from faker.utils.text import slugify
from fastapi import status

from izba_reader import routes

fake = Faker()


@pytest.fixture
def make_url(faker) -> Callable[[str], str]:
    def _make_url(slug: str) -> str:
        return f"https://{faker.domain_name()}/{faker.random_number(digits=5)}/{slug}/"

    return _make_url


@pytest.fixture
def articles(faker, make_url) -> list[dict]:
    articles = []
    for _ in range(fake.random_int(min=10, max=30)):
        title = faker.sentence()[:-1]
        articles.append(
            {
                "title": title,
                "description": faker.paragraph(),
                "url": make_url(slugify(title)),
                "uuid": faker.uuid4(),
            }
        )

        if faker.boolean():
            articles[-1]["date"] = (
                datetime.now() - timedelta(minutes=faker.random_int(30, 90))
            ).strftime("%Y-%m-%d %H:%M")

    return articles


@pytest.fixture
def review(articles, faker):
    return {"recipient": faker.email(), "articles": articles}


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_override")
async def test_ok(async_client, mocked_rollbar, mocker, review):
    mocked_smtplib = mocker.patch(
        "izba_reader.services.mail.smtplib", return_value=Mock()
    )

    response = await async_client.post(routes.MAIL_SEND, json=review)

    assert response.status_code == status.HTTP_202_ACCEPTED, response.json()

    assert (
        review["recipient"]
        in mocked_smtplib.SMTP().__enter__().send_message.call_args[0][0]["To"]
    )

    mocked_rollbar[
        "izba_reader.services.mail.rollbar"
    ].report_message.assert_called_once()
