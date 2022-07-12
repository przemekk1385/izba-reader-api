from datetime import datetime

from pydantic import BaseModel


class Feed(BaseModel):
    title: str
    description: str
    link: str


class News(Feed):
    date: datetime


class MessageResponse(BaseModel):
    detail: str


class HeaderCreateResponse(BaseModel):
    filename: str
