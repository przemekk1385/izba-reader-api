import rollbar
from fastapi import Depends, Request
from fastapi.logger import logger
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from jinja2 import Environment

from izba_reader.constants import BASE_DIR
from izba_reader.decorators import async_report_exceptions
from izba_reader.dependencies import get_settings
from izba_reader.models import Article, Review
from izba_reader.settings import Settings


def _get_connection_config(settings: Settings) -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_TLS=True,
        MAIL_SSL=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=BASE_DIR / "izba_reader" / "templates",
    )


@async_report_exceptions
async def from_template(
    template: str,
    review: Review,
    request: Request,
    settings: Settings = Depends(get_settings),
):
    connection_config = _get_connection_config(settings)

    if settings.environment != "development":
        message = MessageSchema(
            subject="Fastapi-Mail module",
            recipients=[review.recipient],
            template_body=review.articles,
        )

        fm = FastMail(connection_config)
        await fm.send_message(message, template_name="iep.html")
        rollbar.report_message(
            "Email sent",
            level="info",
            extra_data={"email": review.recipient},
            request=request,
        )
    else:
        template_env: Environment = connection_config.template_engine()
        body = template_env.get_template(template).render({"body": review.articles})

        logger.info(f"Email sent to '{review.recipient}'\n\n{body}\n")


@async_report_exceptions
async def as_text(
    review: Review,
    request: Request,
    settings: Settings = Depends(get_settings),
):
    def format_article(article: Article) -> str:
        return f"{article.title}\n{article.description}\n{article.url}"

    body = "\n\n".join(format_article(article) for article in review.articles)

    if settings.environment != "development":
        message = MessageSchema(
            subject=settings.mail_subject, recipients=[review.recipient], body=body
        )

        fm = FastMail(_get_connection_config(settings))
        await fm.send_message(message)
        rollbar.report_message(
            "Email sent",
            level="info",
            extra_data={"email": review.recipient},
            request=request,
        )
    else:
        logger.info(f"Email sent to '{review.recipient}'\n\n{body}\n")


async def dispatch(
    template: str | None,
    review: Review,
    request: Request,
    settings: Settings = Depends(get_settings),
):
    if template is None:
        await as_text(review, request, settings=settings)
    else:
        await from_template(template, review, request, settings=settings)
