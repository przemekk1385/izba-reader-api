import asyncio
from functools import wraps
from typing import Callable, Coroutine
from urllib.parse import urlencode

import httpx
import rollbar
from aioredis import Redis
from fastapi import Depends
from httpx import AsyncClient
from pydantic import AnyUrl, HttpUrl, parse_obj_as
from starlette import status

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
    if response.status_code == status.HTTP_200_OK:
        rollbar.report_message("\u2705 directly", level="info", extra_data={"url": url})
        return {
            "url": url,
            "content": response.text,
        }
    else:
        rollbar.report_message("\u274C directly", level="info", extra_data={"url": url})


async def use_browser(
    browser_url: AnyUrl, client: AsyncClient, urls: list[HttpUrl]
) -> dict[str, HttpUrl | str]:
    response = await client.get(
        f"{browser_url}?{urlencode({'urls[]': urls}, True)}", timeout=30.0
    )
    if response.status_code == status.HTTP_200_OK:
        rollbar.report_message(
            "\u2705 by_browser", level="info", extra_data={"urls": urls}
        )
        return response.json()
    else:
        rollbar.report_message(
            "\u274C by_browser", level="info", extra_data={"urls": urls}
        )


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

        assert isinstance(ret, list)
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
