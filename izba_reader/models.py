from datetime import datetime
from typing import Iterable
from uuid import UUID

from pydantic import BaseModel, EmailStr, HttpUrl, validator, root_validator


class Article(BaseModel):
    title: str
    description: str
    url: HttpUrl


class Message(BaseModel):
    detail: str


class Header(BaseModel):
    size: int
    uuid: UUID


class Review(BaseModel):
    recipient: EmailStr
    articles: list[Article]
