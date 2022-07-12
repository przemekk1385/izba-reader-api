import itertools
import sys
from datetime import date
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
    Query,
    Request,
    UploadFile,
    status,
)
from pydantic import EmailStr, HttpUrl, Required
from rollbar.contrib.fastapi import add_to as rollbar_add_to
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from izba_reader import constants, routes
from izba_reader.dependencies import get_redis, get_settings
from izba_reader.models import Feed, HeaderCreateResponse, MessageResponse, News
from izba_reader.rollbar_handlers import ignore_handler
from izba_reader.services import fetch, mail
from izba_reader.services.parser import get_parser
from izba_reader.settings import Settings

if not constants.MEDIA_ROOT.is_dir():
    constants.MEDIA_ROOT.mkdir()

app = FastAPI()

rollbar_add_to(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=constants.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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


@app.get(
    routes.HEALTH_LIST,
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


@app.get(routes.HEADER_LIST, response_model=list[HttpUrl])
def header_list(request: Request):
    return [
        f"{str(request.base_url)[:-1]}{constants.MEDIA_URL}{header.name}"
        for header in constants.MEDIA_ROOT.glob("**/*")
        if header.is_file()
    ]


@app.post(
    routes.HEADER_LIST,
    responses={status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {"model": MessageResponse}},
    response_model=HeaderCreateResponse,
)
async def header_create(
    request: Request, uploaded_file: UploadFile = File(...)
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


@app.get(routes.MAIL_SEND, response_model=None, status_code=status.HTTP_202_ACCEPTED)
async def mail_send(
    background_tasks: BackgroundTasks,
    email: EmailStr,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    background_tasks.add_task(mail.send, email, request, settings=settings)


@app.get(
    routes.FEED_LIST,
    response_model=list[Feed],
)
async def feed_list(
    urls: list[HttpUrl] = Query(default=Required),
) -> list[dict]:
    rss = await fetch.rss(urls)

    return list(
        itertools.chain(*[get_parser(url.host)(feed) for url, feed in rss.items()])
    )


@app.get(
    routes.NEWS_LIST,
    response_model=list[News],
)
async def news_list(
    dt: date,
    urls: list[HttpUrl] = Query(default=Required),
) -> list[dict]:
    html = await fetch.html(urls)

    return [
        entry
        for entry in itertools.chain(
            *[get_parser(url.host)(page) for url, page in html.items()]
        )
        if entry["date"].date() == dt
    ]
