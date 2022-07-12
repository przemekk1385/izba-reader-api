import asyncio
from functools import wraps
from typing import Callable, Coroutine

import httpx
import rollbar
from aioredis import Redis
from httpx import AsyncClient
from pydantic import HttpUrl
from starlette import status

from izba_reader.dependencies import get_redis, get_settings
from izba_reader.services.utils import launch_browser
from izba_reader.settings import Settings


def fetch_cached(
    func: Callable,
) -> Callable[
    [list[HttpUrl], Redis, Settings],
    Coroutine[None, None, dict[HttpUrl, str]],
]:
    @wraps(func)
    async def wrapper(
        urls: list[HttpUrl],
    ) -> dict[HttpUrl, str]:
        settings = get_settings()
        redis = get_redis(settings)

        cached_results = {key: await redis.get(str(key)) for key in urls}

        if all(cached_results.values()):
            return cached_results
        else:
            results = await func(urls)
            for key in results.keys():
                await redis.set(
                    str(key),
                    results[key],
                    ex=settings.ex,
                )
            return results

    return wrapper


@fetch_cached
async def html(urls: list[HttpUrl]) -> dict[HttpUrl, str]:
    async def get_content(url: HttpUrl) -> Coroutine:
        page = await browser.newPage()
        await page.goto(url, {"waitUntil": ["domcontentloaded", "networkidle0"]})

        rollbar.report_message(f"\u2705 '{url}'")

        return page.content()

    async with launch_browser() as browser:
        pages = await asyncio.gather(*[await get_content(url) for url in urls])

    assert isinstance(pages, list)
    return {url: page for url, page in zip(urls, pages)}


@fetch_cached
async def rss(urls: list[HttpUrl]) -> dict[HttpUrl, str]:
    async def get_text(client_: AsyncClient, url: str) -> str:
        response = await client_.get(url, follow_redirects=True)
        if response.status_code == status.HTTP_200_OK:
            rollbar.report_message(f"\u2705 '{url}'")
            return response.text
        else:
            rollbar.report_message(f"\u274C '{url}'")

    async with httpx.AsyncClient() as client:
        feeds = await asyncio.gather(
            *[asyncio.ensure_future(get_text(client, url)) for url in urls]
        )

    assert isinstance(feeds, list)
    return {url: feed for url, feed in zip(urls, feeds) if feed}
