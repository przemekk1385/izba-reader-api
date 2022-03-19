from datetime import datetime

from pydantic import BaseModel


class RssFeed(BaseModel):
    title: str
    description: str
    link: str


class RssFeedsResponse(BaseModel):
    fetched_at: datetime
    feeds_count: int
    feeds: list[RssFeed]
