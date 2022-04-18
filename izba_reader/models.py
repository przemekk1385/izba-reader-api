from datetime import datetime

from pydantic import BaseModel


class Feed(BaseModel):
    title: str
    description: str
    link: str


class News(Feed):
    date: datetime


class BaseServiceResponseModel(BaseModel):
    time: datetime
    count: int


class RssFeedsResponse(BaseServiceResponseModel):
    items: list[Feed]


class WebScrapersResponse(BaseServiceResponseModel):
    items: list[News]


class HeadersListResponse(BaseModel):
    __root__: list[str]


class MessageResponse(BaseModel):
    detail: str


class UploadImageResponse(BaseModel):
    filename: str
