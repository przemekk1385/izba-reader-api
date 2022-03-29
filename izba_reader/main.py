import itertools
from datetime import datetime
from uuid import uuid4

import cv2
import numpy as np
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile, status

from izba_reader import routes, timezones
from izba_reader.constants import IMAGES_DIR
from izba_reader.models import (
    Message,
    RssFeedsResponse,
    UploadImageResponse,
    WebScrapersResponse,
)
from izba_reader.services.cache import get_cache, set_cache
from izba_reader.tasks import fetch_rss_feeds, scrap_web

app = FastAPI()

if not IMAGES_DIR.is_dir():
    IMAGES_DIR.mkdir()


@app.get("/")
def hello_world() -> dict:
    return {"hello": "world"}


@app.get(routes.RSS_FEEDS, response_model=RssFeedsResponse)
async def rss_feeds(background_tasks: BackgroundTasks) -> dict:
    key = routes.RSS_FEEDS
    ret = await get_cache(key)

    if not ret:
        feeds = list(itertools.chain(*await fetch_rss_feeds()))
        ret = {
            "fetched_at": datetime.now().astimezone(timezones.EUROPE_WARSAW),
            "feeds_count": len(feeds),
            "feeds": feeds,
        }

        background_tasks.add_task(set_cache, key, ret)

    return ret


@app.get(routes.WEB_SCRAPERS, response_model=WebScrapersResponse)
async def web_scrapers(background_tasks: BackgroundTasks) -> dict:
    key = routes.WEB_SCRAPERS
    ret = await get_cache(key)

    if not ret:
        news = list(itertools.chain(*await scrap_web()))
        ret = {
            "news_count": len(news),
            "news": news,
        }

        background_tasks.add_task(set_cache, key, ret)

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

    path = IMAGES_DIR / f"{uuid4()}.jpg"
    cv2.imwrite(str(path), img)

    return {"filename": path.name}
