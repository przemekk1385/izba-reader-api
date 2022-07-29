from functools import singledispatch

import rollbar
from fastapi import Depends, Request
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import BaseModel

from izba_reader.decorators import async_report_exceptions
from izba_reader.dependencies import get_settings
from izba_reader.models import Feed, News, Review
from izba_reader.settings import Settings


def _make_text_message(articles: list[Feed | News]) -> str:
    @singledispatch
    def format_article(article: BaseModel) -> str:
        pass

    @format_article.register
    def format_feed(article: Feed) -> str:
        return (
            "#feed\n" f"{article.title}\n" f"{article.description}\n" f"{article.url}"
        )

    @format_article.register
    def format_news(article: News) -> str:
        return (
            "#web\n"
            f"{article.date}\n"
            f"{article.title}\n"
            f"{article.description}\n"
            f"{article.url}"
        )

    return "\n\n".join(format_article(article) for article in articles)


@async_report_exceptions
async def send(
    review: Review,
    request: Request,
    settings: Settings = Depends(get_settings),
):
    body = _make_text_message(review.articles)

    message = MessageSchema(
        subject=settings.mail_subject, recipients=[review.recipient], body=body
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
        "Email sent",
        level="info",
        extra_data={"email": review.recipient},
        request=request,
    )
