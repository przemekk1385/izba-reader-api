from functools import singledispatch

import rollbar
from fastapi import Depends, Request
from fastapi.logger import logger
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

from izba_reader.decorators import async_report_exceptions
from izba_reader.dependencies import get_settings
from izba_reader.models import Article, Review
from izba_reader.settings import Settings


def _make_text_message(articles: list[Article]) -> str:
    @singledispatch
    def format_article(article: Article) -> str:
        return f"{article.title}\n{article.description}\n{article.url}"

    return "\n\n".join(format_article(article) for article in articles)


@async_report_exceptions
async def send(
    review: Review,
    request: Request,
    settings: Settings = Depends(get_settings),
):
    body = _make_text_message(review.articles)

    if settings.environment != "development":
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
    else:
        logger.info(f"Email sent to '{review.recipient}'\n\n{body}\n")
