from datetime import datetime

import sentry_sdk
from aioredis import Redis
from aioredis.exceptions import ConnectionError
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from izba_reader import constants, routes
from izba_reader.constants import URLS
from izba_reader.dependencies import get_api_key, get_redis, get_settings
from izba_reader.models import Article, Review
from izba_reader.openapi import custom_openapi
from izba_reader.services import documents, mail
from izba_reader.services.parser import get_parser
from izba_reader.settings import Settings
from izba_reader.utils import get_border_date, get_env

sentry_dsn = get_env("SENTRY_DSN")
environment = get_env("ENVIRONMENT")

sentry_sdk.init(
    dsn=sentry_dsn,
    environment=environment,
    traces_sample_rate=1.0,
)

_settings = get_settings()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.openapi = custom_openapi


@app.get(
    routes.HEALTH_LIST,
    dependencies=[Depends(get_api_key)],
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": None}},
    response_model=None,
)
async def health(
    redis: Redis = Depends(get_redis),
) -> None:
    try:
        await redis.ping()
    except ConnectionError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


@app.post(
    routes.MAIL_SEND,
    dependencies=[Depends(get_api_key)],
    response_model=None,
    status_code=status.HTTP_202_ACCEPTED,
)
async def mail_send(
    background_tasks: BackgroundTasks,
    request: Request,
    review: Review,
    settings: Settings = Depends(get_settings),
) -> None:
    background_tasks.add_task(mail.send, review, request, settings)


@app.get(
    routes.ARTICLE_LIST,
    response_model=list[Article],
    response_model_exclude_defaults=False,
)
async def article_list(
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> list[dict]:
    ret = []
    for url, document in (
        await documents.fetch(URLS, redis=redis, settings=settings)
    ).items():
        parser = get_parser(url.host)

        all_articles = parser(document)
        latest_articles = [
            article
            for article in all_articles
            if article.get("date", datetime.now()).date() >= get_border_date()
        ]

        if latest_articles:
            ret.extend(latest_articles)
        else:
            ret.extend(all_articles[: constants.FALLBACK_ARTICLES_COUNT])

    return ret
