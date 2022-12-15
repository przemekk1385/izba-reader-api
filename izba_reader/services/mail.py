import smtplib
from email.message import EmailMessage

from fastapi import Depends, Request

from izba_reader.decorators import capture_background_task_exception
from izba_reader.dependencies import get_settings
from izba_reader.models import Article, Review
from izba_reader.settings import Settings


@capture_background_task_exception
async def send(
    review: Review, request: Request, settings: Settings = Depends(get_settings)
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
