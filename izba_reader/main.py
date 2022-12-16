import base64
import itertools
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

import cv2
import numpy as np
import sentry_sdk
from aioredis import Redis
from aioredis.exceptions import ConnectionError
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import APIKey
from fastapi.staticfiles import StaticFiles

from izba_reader import constants, routes
from izba_reader.constants import SITES
from izba_reader.dependencies import get_api_key, get_redis, get_settings
from izba_reader.models import Article, Header, Message, Review
from izba_reader.openapi import custom_openapi
from izba_reader.services import fetch, mail
from izba_reader.services.parser import get_parser
from izba_reader.settings import Settings

if not constants.MEDIA_ROOT.is_dir():
    constants.MEDIA_ROOT.mkdir()


def set_up_app() -> FastAPI:
    settings = get_settings()

    app_ = FastAPI()
    app_.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=1.0,
    )

    return app_


app = set_up_app()
app.mount(
    constants.MEDIA_URL,
    StaticFiles(directory=constants.MEDIA_ROOT),
    name=constants.MEDIA_ROOT.name,
)
app.openapi = custom_openapi


@app.get(
    routes.HEALTH_LIST,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": None}},
    response_model=None,
)
async def health(
    request: Request,
    api_key: APIKey = Depends(get_api_key),
    redis: Redis = Depends(get_redis),
) -> None:
    try:
        await redis.ping()
    except ConnectionError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


@app.get(routes.HEADER_LIST, response_model=list[UUID])
def header_list(api_key: APIKey = Depends(get_api_key)):
    return [
        header.stem for header in constants.MEDIA_ROOT.glob("**/*") if header.is_file()
    ]


@app.post(
    routes.HEADER_LIST,
    responses={status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {"model": Message}},
    response_model=Header,
)
async def header_create(
    request: Request,
    api_key: APIKey = Depends(get_api_key),
    uploaded_file: UploadFile = File(...),
) -> dict:
    async def get_opencv_img_from_buffer(buffer, flags):
        bytes_as_np_array = np.frombuffer(await buffer.read(), dtype=np.uint8)
        return cv2.imdecode(bytes_as_np_array, flags)

    if uploaded_file.content_type != "image/jpeg":
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unhandled MIME type '{uploaded_file.content_type}'",
        )

    img = await get_opencv_img_from_buffer(uploaded_file, cv2.IMREAD_UNCHANGED)
    aspect_ratio = (
        round(img.shape[1] / (img.shape[1] - img.shape[0])),
        round(img.shape[0] / (img.shape[1] - img.shape[0])),
    )

    if aspect_ratio != (4, 3):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="4:3 aspect ratio image required",
        )

    if img.shape[1] > 1000:
        img = cv2.resize(img, (1000, 750))

    path = constants.MEDIA_ROOT / f"{uuid4()}.jpg"
    cv2.imwrite(str(path), img)

    return {"size": img.size, "uuid": path.stem}


@app.get(
    routes.HEADER_DETAIL,
    responses={status.HTTP_404_NOT_FOUND: {"model": Message}},
    response_model=bytes,
)
def header_retrieve(identifier: UUID, api_key: APIKey = Depends(get_api_key)) -> bytes:
    try:
        with open(constants.MEDIA_ROOT / f"{identifier}.jpg", "rb") as img_file:
            return base64.b64encode(img_file.read())
    except FileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Header '{identifier}' not found",
        ) from exc


@app.post(routes.MAIL_SEND, response_model=None, status_code=status.HTTP_202_ACCEPTED)
async def mail_send(
    background_tasks: BackgroundTasks,
    review: Review,
    request: Request,
    api_key: APIKey = Depends(get_api_key),
    settings: Settings = Depends(get_settings),
) -> None:
    background_tasks.add_task(mail.send, review, request, settings=settings)


@app.get(
    routes.ARTICLE_LIST,
    response_model=list[Article],
    response_model_exclude_defaults=False,
)
async def article_list(
    api_key: APIKey = Depends(get_api_key),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> list[Article]:
    articles = await fetch.get_sites(SITES, redis=redis, settings=settings)
    dt = date.today() - timedelta(days=1)

    return [
        article
        for article in itertools.chain(
            *[get_parser(url.host)(feed) for url, feed in articles.items()]
        )
        if article.get("date", datetime.now()).date() >= dt
    ]


@app.get(
    routes.SENTRY_DEBUG,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": None}},
    response_model=None,
)
async def sentry_debug(settings: Settings = Depends(get_settings)):
    if settings.environment == "development":
        _ = 1 / 0
