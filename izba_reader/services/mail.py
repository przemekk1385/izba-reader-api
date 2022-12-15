import smtplib
from email.message import EmailMessage

import rollbar
from fastapi import Depends, Request

from izba_reader.decorators import async_report_exceptions
from izba_reader.dependencies import get_settings
from izba_reader.models import Article, Review


@async_report_exceptions
async def send(
    review: Review, request: Request, settings: Depends(get_settings)
) -> None:
    def format_article(article: Article) -> str:
        return f"{article.title}\n{article.description}\n{article.url}"

    message = EmailMessage()
    message.set_content(
        "\n\n".join(format_article(article) for article in review.articles)
    )
    message["To"] = review.recipient
    message["From"] = settings.mail_from
    message["Subject"] = settings.mail_subject

    with smtplib.SMTP() as server:
        server.connect(settings.mail_server, settings.mail_port)
        server.login(settings.mail_username, settings.mail_password)
        server.send_message(message)

        rollbar.report_message(
            "Email sent",
            level="info",
            extra_data={"email": review.recipient},
            request=request,
        )
