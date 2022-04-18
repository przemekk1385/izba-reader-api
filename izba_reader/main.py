import sys
from uuid import uuid4

import cv2
import numpy as np
import rollbar
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
from pydantic import EmailStr
from rollbar.contrib.fastapi import add_to as rollbar_add_to
from starlette.staticfiles import StaticFiles

from izba_reader import constants, routes
from izba_reader.dependencies import get_redis, get_settings
from izba_reader.models import (
    HeadersListResponse,
    MessageResponse,
    RssFeedsResponse,
    UploadImageResponse,
    WebScrapersResponse,
)
from izba_reader.rollbar_handlers import ignore_handler
from izba_reader.services.mail import send_message
from izba_reader.settings import Settings
from izba_reader.tasks import get_from_html, get_from_rss

if not constants.MEDIA_ROOT.is_dir():
    constants.MEDIA_ROOT.mkdir()

app = FastAPI()

rollbar_add_to(app)

app.mount(
    constants.MEDIA_URL,
    StaticFiles(directory=constants.MEDIA_ROOT),
    name=constants.MEDIA_ROOT.name,
)


@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    rollbar.init(settings.rollbar_access_token, settings.environment)
    rollbar.events.add_payload_handler(ignore_handler)


@app.get(routes.HEADERS, response_model=HeadersListResponse)
def headers(request: Request):
    return [
        f"{str(request.base_url)[:-1]}{constants.MEDIA_URL}{header.name}"
        for header in constants.MEDIA_ROOT.glob("**/*")
        if header.is_file()
    ]


@app.get(
    routes.HEALTH,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": None}},
    response_model=None,
)
async def health(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> None:
    rollbar.report_message("Ping", level="info", request=request)
    try:
        await redis.ping()
    except ConnectionError:
        rollbar.report_exc_info(sys.exc_info(), request)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    else:
        rollbar.report_message("Pong", level="info", request=request)


@app.get(routes.RSS_FEEDS, response_model=RssFeedsResponse)
async def rss_feeds(
    background_tasks: BackgroundTasks,
    request: Request,
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> dict:
    feeds = await get_from_rss(
        background_tasks, request, redis=redis, settings=settings
    )

    return {**feeds, "count": len(feeds["items"])}


@app.get(routes.WEB_SCRAPERS, response_model=WebScrapersResponse)
async def web_scrapers(
    background_tasks: BackgroundTasks,
    request: Request,
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> dict:
    news = await get_from_html(
        background_tasks, request, redis=redis, settings=settings
    )

    return {**news, "count": len(news["items"])}


@app.post(
    routes.UPLOAD_IMAGE,
    responses={status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {"model": MessageResponse}},
    response_model=UploadImageResponse,
)
async def upload_image(request: Request, uploaded_file: UploadFile = File(...)) -> dict:
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

    path = constants.MEDIA_ROOT / f"{uuid4()}.jpg"
    cv2.imwrite(str(path), img)

    rollbar.report_message(
        "Image uploaded", level="info", extra_data={"name": path.name}, request=request
    )

    return {"filename": f"{constants.MEDIA_URL}{path.name}"}


@app.get(routes.SEND_MAIL, response_model=None, status_code=status.HTTP_202_ACCEPTED)
async def send_mail(
    background_tasks: BackgroundTasks,
    email: EmailStr,
    request: Request,
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> None:
    background_tasks.add_task(
        send_message, background_tasks, email, request, redis=redis, settings=settings
    )
    # await send_message()
