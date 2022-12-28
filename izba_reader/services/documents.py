import asyncio
from functools import singledispatch
from urllib.parse import urlencode

import httpx
from aioredis import Redis
from fastapi import Depends
from httpx import AsyncClient, HTTPStatusError
from pydantic import HttpUrl, parse_obj_as
from sentry_sdk import capture_exception
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from izba_reader.constants import BrowsableUrl
from izba_reader.dependencies import get_redis, get_settings
from izba_reader.settings import Settings


@retry(
    reraise=True,
    retry=retry_if_exception_type(httpx.ReadTimeout),
    stop=stop_after_attempt(6),
    wait=wait_exponential(min=1, max=16),
)
@singledispatch
async def _fetch(
    url: HttpUrl,
    client: AsyncClient,
    settings: Settings = Depends(get_settings),
):
    pass


@_fetch.register
async def _fetch_directly(
    url: HttpUrl, client: AsyncClient, settings: Settings = Depends(get_settings)
) -> dict[str, HttpUrl | str]:
    response = await client.get(url, follow_redirects=True)

    try:
        response.raise_for_status()
    except HTTPStatusError as http_status_error:
        capture_exception(http_status_error)
        message = {"url": url, "content": ""}
    else:
        message = {
            "url": url,
            "content": response.text,
        }

    return message


@_fetch.register
async def _fetch_using_browser(
    url: BrowsableUrl, client: AsyncClient, settings: Settings = Depends(get_settings)
) -> dict[str, BrowsableUrl | str]:
    response = await client.get(f"{settings.browser_url}?{urlencode({'urls': url})}")

    try:
        response.raise_for_status()
    except HTTPStatusError as http_status_error:
        capture_exception(http_status_error)
        return {"url": url, "content": ""}

    return [
        {
            "url": parse_obj_as(BrowsableUrl, article["url"]),
            "content": article["content"],
        }
        for article in response.json()
    ][0]


async def fetch(
    urls: list[HttpUrl | tuple[HttpUrl, ...]],
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> dict[HttpUrl, str]:
    cached_contents = {url: await redis.get(str(url)) for url in urls}

    transport = httpx.AsyncHTTPTransport(retries=3)
    async with httpx.AsyncClient(transport=transport) as client:

        documents = await asyncio.gather(
            *[
                _fetch(url, client, settings=settings)
                for url in urls
                if not cached_contents[url]
            ],
            return_exceptions=True,
        )

        failed = []
        for i, item in enumerate(documents):
            if isinstance(item, Exception):
                capture_exception(item)
                failed.append(i)

        for i in failed[::-1]:
            del documents[i]

        for document in documents:
            await redis.set(
                str(document["url"]),
                document["content"],
                ex=settings.ex,
            )

        return {document["url"]: document["content"] for document in documents}
