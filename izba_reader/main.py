import itertools
from datetime import datetime

from fastapi import FastAPI

from izba_reader.models import RssFeedsResponse
from izba_reader.tasks import fetch_rss_task

app = FastAPI()


@app.get("/")
def hello_world():
    return {"hello": "world"}


@app.get("/rss_feeds", response_model=RssFeedsResponse)
async def rss_feeds():
    feeds = list(itertools.chain(*await fetch_rss_task()))

    return {
        "fetched_at": datetime.now().strftime("%Y-%m-%d %X"),
        "feeds_count": len(feeds),
        "feeds": feeds,
    }
