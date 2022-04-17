import rollbar
from aioredis import Redis
from fastapi import BackgroundTasks, Depends, Request
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr

from izba_reader.dependencies import get_redis, get_settings
from izba_reader.settings import Settings
from izba_reader.tasks import get_both


async def make_text_message(
    background_tasks: BackgroundTasks,
    request: Request,
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> str:
    feeds, news = await get_both(
        background_tasks, request, redis=redis, settings=settings
    )

    return "\n\n".join(
        [
            "\n\n".join(
                [
                    "#rss\n"
                    f"{item['title']}\n"
                    f"{item['description']}\n"
                    f"{item['link']}"
                    for item in feeds["items"]
                ]
                if feeds["items"]
                else ["no #rss"]
            ),
            "\n\n".join(
                [
                    "#web\n"
                    f"{item['date']}\n"
                    f"{item['title']}\n"
                    f"{item['description']}\n"
                    f"{item['link']}"
                    for item in news["items"]
                ]
                if news["items"]
                else ["no #web"]
            ),
        ]
    )


async def send_message(
    background_tasks: BackgroundTasks,
    email: EmailStr,
    request: Request,
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
):
    body = await make_text_message(
        background_tasks, request, redis=redis, settings=settings
    )

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
