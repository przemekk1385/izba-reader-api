import itertools
from datetime import datetime

from fastapi import BackgroundTasks, FastAPI

from izba_reader import routes, timezones
from izba_reader.models import WebScrapersResponse
from izba_reader.services.cache import get_cache, set_cache
from izba_reader.tasks import fetch_rss_feeds, scrap_web

app = FastAPI()


@app.get("/")
def hello_world() -> dict:
    return {"hello": "world"}


@app.get(routes.RSS_FEEDS)
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
