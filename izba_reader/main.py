import itertools
from datetime import datetime

from fastapi import FastAPI

from izba_reader import timezones
from izba_reader.models import RssFeedsResponse, WebScrapersResponse
from izba_reader.tasks import fetch_rss_feeds, scrap_web

app = FastAPI()


@app.get("/")
def hello_world():
    return {"hello": "world"}


@app.get("/rss_feeds", response_model=RssFeedsResponse)
async def rss_feeds():
    feeds = list(itertools.chain(*await fetch_rss_feeds()))

    return {
        "fetched_at": datetime.now().astimezone(timezones.EUROPE_WARSAW),
        "feeds_count": len(feeds),
        "feeds": feeds,
    }


@app.get("/web_scrapers", response_model=WebScrapersResponse)
async def web_scrapers():
    news = list(itertools.chain(*await scrap_web()))

    return {
        "news_count": len(news),
        "news": news,
    }
