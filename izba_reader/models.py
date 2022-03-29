from datetime import datetime

from pydantic import BaseModel


class Message(BaseModel):
    detail: str


class Feed(BaseModel):
    title: str
    description: str
    link: str


class News(Feed):
    date: datetime


class RssFeedsResponse(BaseModel):
    fetched_at: datetime
    feeds_count: int
    feeds: list[Feed]


class UploadImageResponse(BaseModel):
    filename: str


class WebScrapersResponse(BaseModel):
    news_count: int
    news: list[News]
