import asyncio
from functools import wraps
from typing import Callable, Coroutine
from urllib.parse import urlencode

import httpx
from aioredis import Redis
from fastapi import Depends
from httpx import AsyncClient, HTTPStatusError
from pydantic import AnyUrl, HttpUrl, parse_obj_as
from sentry_sdk import capture_exception

from izba_reader.constants import Site
from izba_reader.dependencies import get_redis, get_settings
from izba_reader.settings import Settings


def fetch_cached(
    func: Callable,
) -> Callable[[list[Site], Redis, Settings], Coroutine[None, None, dict[HttpUrl, str]]]:
    @wraps(func)
    async def wrapper(
        sites: list[Site],
        redis: Redis = Depends(get_redis),
        settings: Settings = Depends(get_settings),
    ) -> dict[HttpUrl, str]:
        cached_results = {site.url: await redis.get(str(site.url)) for site in sites}

        if all(cached_results.values()):
            return cached_results
        else:
            results = await func(sites, redis=redis, settings=settings)
            for key in results.keys():
                await redis.set(
                    str(key),
                    results[key],
                    ex=settings.ex,
                )
            return results

    return wrapper


async def fetch_directly(client: AsyncClient, url: HttpUrl) -> dict[str, HttpUrl | str]:
    response = await client.get(url, follow_redirects=True)

    try:
        response.raise_for_status()
    except HTTPStatusError as http_status_error:
        capture_exception(http_status_error)
        return {"url": url, "content": ""}

    return {
        "url": url,
        "content": response.text,
    }


async def use_browser(
    browser_url: AnyUrl, client: AsyncClient, urls: list[HttpUrl]
) -> list[str, HttpUrl | str]:
    response = await client.get(
        f"{browser_url}?{urlencode({'urls[]': urls}, True)}", timeout=30.0
    )

    try:
        response.raise_for_status()
    except HTTPStatusError as http_status_error:
        capture_exception(http_status_error)
        return []

    return response.json()


@fetch_cached
async def get_sites(
    sites: list[Site],
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> dict[HttpUrl, str]:
    async with httpx.AsyncClient() as client:
        ret = await asyncio.gather(
            *[
                asyncio.ensure_future(fetch_directly(client, source.url))
                for source in sites
                if not source.use_browser
            ],
        )

        ret.extend(
            [
                {
                    "url": parse_obj_as(HttpUrl, article["url"]),
                    "content": article["content"],
                }
                for article in await use_browser(
                    settings.browser_url,
                    client,
                    [s.url for s in sites if s.use_browser],
                )
            ]
        )

    return {site["url"]: site["content"] for site in ret}
