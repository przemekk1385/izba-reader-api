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


class BaseResponseModel(BaseModel):
    time: datetime
    count: int


class RssFeedsResponse(BaseResponseModel):
    items: list[Feed]


class WebScrapersResponse(BaseResponseModel):
    items: list[News]


class UploadImageResponse(BaseModel):
    filename: str
