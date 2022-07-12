import itertools

import rollbar
from fastapi import Depends, Request
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr

from izba_reader.constants import FEED_URLS, NEWS_URLS
from izba_reader.decorators import async_report_exceptions
from izba_reader.dependencies import get_settings
from izba_reader.services import fetch
from izba_reader.settings import Settings


async def _make_text_message() -> str:
    feeds, news = await fetch.rss(FEED_URLS), await fetch.html(NEWS_URLS)

    return "\n\n".join(
        [
            "\n\n".join(
                [
                    "#rss\n"
                    f"{item['title']}\n"
                    f"{item['description']}\n"
                    f"{item['link']}"
                    for item in itertools.chain(*feeds.values())
                ]
                if feeds
                else ["no #rss"]
            ),
            "\n\n".join(
                [
                    "#web\n"
                    f"{item['date']}\n"
                    f"{item['title']}\n"
                    f"{item['description']}\n"
                    f"{item['link']}"
                    for item in itertools.chain(*news.values())
                ]
                if news
                else ["no #web"]
            ),
        ]
    )


@async_report_exceptions
async def send(
    email: EmailStr,
    request: Request,
    settings: Settings = Depends(get_settings),
):
    body = await _make_text_message()

    message = MessageSchema(
        subject=settings.mail_subject, recipients=[email], body=body
    )

    connection_config = ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_TLS=True,
        MAIL_SSL=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )

    fm = FastMail(connection_config)
    await fm.send_message(message)
    rollbar.report_message(
        "Email sent", level="info", extra_data={"email": email}, request=request
    )
