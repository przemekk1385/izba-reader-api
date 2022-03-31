import asyncio
import itertools
from datetime import datetime
from uuid import uuid4

import cv2
import httpx
import numpy as np
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
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from starlette.staticfiles import StaticFiles

from izba_reader import constants, routes, timezones
from izba_reader.models import (
    Message,
    RssFeedsResponse,
    UploadImageResponse,
    WebScrapersResponse,
)
from izba_reader.services.cache import get_cache, get_redis, set_cache
from izba_reader.settings import Settings, get_settings
from izba_reader.tasks import fetch_rss_feeds, scrap_web

app = FastAPI()

if not constants.IMAGES_ROOT.is_dir():
    constants.IMAGES_ROOT.mkdir()

app.mount(
    constants.IMAGES_URL,
    StaticFiles(directory=constants.IMAGES_ROOT),
    name=constants.IMAGES_ROOT.name,
)


@app.get(
    routes.HEALTH,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": None}},
    response_model=None,
)
async def health(redis: Redis = Depends(get_redis)) -> None:
    try:
        await redis.ping()
    except ConnectionError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


@app.get(routes.RSS_FEEDS, response_model=RssFeedsResponse)
async def rss_feeds(
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    redis: Redis = Depends(get_redis),
) -> dict:
    key = routes.RSS_FEEDS
    ret = await get_cache(key, redis=redis)

    if not ret:
        feeds = list(itertools.chain(*await fetch_rss_feeds()))
        ret = {
            "fetched_at": datetime.now().astimezone(timezones.EUROPE_WARSAW),
            "feeds_count": len(feeds),
            "feeds": feeds,
        }

        background_tasks.add_task(set_cache, key, ret, settings=settings, redis=redis)

    return ret


@app.get(routes.WEB_SCRAPERS, response_model=WebScrapersResponse)
async def web_scrapers(
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    redis: Redis = Depends(get_redis),
) -> dict:
    key = routes.WEB_SCRAPERS
    ret = await get_cache(key, redis=redis)

    if not ret:
        news = list(itertools.chain(*await scrap_web()))
        ret = {
            "news_count": len(news),
            "news": news,
        }

        background_tasks.add_task(set_cache, key, ret, settings=settings, redis=redis)

    return ret


@app.post(
    routes.UPLOAD_IMAGE,
    responses={status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {"model": Message}},
    response_model=UploadImageResponse,
)
async def upload_image(uploaded_file: UploadFile = File(...)) -> dict:
    async def get_opencv_img_from_buffer(buffer, flags):
        bytes_as_np_array = np.frombuffer(await buffer.read(), dtype=np.uint8)
        return cv2.imdecode(bytes_as_np_array, flags)

    if uploaded_file.content_type != "image/jpeg":
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unhandled MIME type '{uploaded_file.content_type}'",
        )

    img = await get_opencv_img_from_buffer(uploaded_file, cv2.IMREAD_UNCHANGED)
    aspect_ratio = img.shape[1] / img.shape[0]

    if aspect_ratio != 4 / 3:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="4:3 aspect ratio image required",
        )

    if img.shape[1] > 1000:
        img = cv2.resize(img, (1000, 750))

    path = constants.IMAGES_ROOT / f"{uuid4()}.jpg"
    cv2.imwrite(str(path), img)

    return {"filename": f"{constants.IMAGES_URL}{path.name}"}


@app.get(routes.SEND_MAIL, response_model=None)
async def send_mail(
    email: str, request: Request, settings: Settings = Depends(get_settings)
) -> None:
    base_url = str(request.base_url)[:-1]
    async with httpx.AsyncClient() as client:
        rss_feeds_response, web_scrapers_response = await asyncio.gather(
            client.get(f"{base_url}{routes.RSS_FEEDS}"),
            client.get(f"{base_url}{routes.WEB_SCRAPERS}"),
        )

        feeds = rss_feeds_response.json()["feeds"]
        news = web_scrapers_response.json()["news"]

        body = "\n\n".join(
            [
                "\n\n".join(
                    [
                        "source:RSS\n"
                        f"{item['title']}\n"
                        f"{item['description']}\n"
                        f"{item['link']}"
                        for item in feeds
                    ]
                ),
                "\n\n".join(
                    [
                        "source:WEB\n"
                        f"{item['date']}\n"
                        f"{item['title']}\n"
                        f"{item['description']}\n"
                        f"{item['link']}"
                        for item in news
                    ]
                ),
            ]
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
