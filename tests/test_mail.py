from datetime import datetime, timedelta
from typing import Callable
from urllib.parse import urlencode

import pytest
from faker import Faker
from faker.utils.text import slugify
from fastapi import status
from fastapi_mail import FastMail

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
@pytest.mark.parametrize("template", (None, "iep.html"))
@pytest.mark.usefixtures("settings_override")
async def test_ok(template, async_client, mocked_rollbar, mocker, review):
    mocked_send_message = mocker.patch.object(FastMail, "send_message")

    url = (
        f"{routes.MAIL_SEND}?{urlencode({'template': template})}"
        if template
        else routes.MAIL_SEND
    )
    response = await async_client.post(url, json=review)

    assert response.status_code == status.HTTP_202_ACCEPTED, response.json()

    assert review["recipient"] in mocked_send_message.call_args[0][0].recipients

    mocked_rollbar[
        "izba_reader.services.send_mail.rollbar"
    ].report_message.assert_called_once()
