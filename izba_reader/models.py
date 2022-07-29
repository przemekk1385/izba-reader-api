from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, HttpUrl, validator


class Feed(BaseModel):
    title: str
    description: str
    url: HttpUrl


class News(Feed):
    date: datetime


class Review(BaseModel):
    recipient: EmailStr
    articles: list[Feed | News]

    @validator("articles", pre=True)
    def select_model(cls, articles: list[dict]) -> list[Feed | News]:
        return [News(**item) if item.get("date") else Feed(**item) for item in articles]


class Message(BaseModel):
    detail: str


class Header(BaseModel):
    size: int
    uuid: UUID
