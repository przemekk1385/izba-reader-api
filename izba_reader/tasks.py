import asyncio

import httpx
import rollbar
from aioredis import Redis
from fastapi import BackgroundTasks, Depends, Request

from izba_reader.cache import get_cache, set_cache
from izba_reader.dependencies import get_redis, get_settings
from izba_reader.services import html, rss
from izba_reader.services.html import get_browser
from izba_reader.settings import Settings
from izba_reader.utils import gather_services


async def get_both(
    background_tasks: BackgroundTasks,
    request: Request,
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> tuple[dict, ...]:
    return await asyncio.gather(
        get_from_rss(background_tasks, request, redis=redis, settings=settings),
        get_from_html(background_tasks, request, redis=redis, settings=settings),
    )


async def get_from_rss(
    background_tasks: BackgroundTasks,
    request: Request,
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> dict:
    key = "get_from_rss"

    if ret := await get_cache(key, redis=redis):
        rollbar.report_message("Got cached RSS feeds", level="info", request=request)
        return ret

    async with httpx.AsyncClient() as client:
        ret = await gather_services(
            *[
                getattr(rss, rss_service_name)(client)
                for rss_service_name in rss.__all__
            ]
        )

        background_tasks.add_task(set_cache, key, ret, redis=redis, settings=settings)
        rollbar.report_message("Got fresh RSS feeds", level="info", request=request)

    return ret


async def get_from_html(
    background_tasks: BackgroundTasks,
    request: Request,
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> dict:
    key = "get_from_html"

    if ret := await get_cache(key, redis=redis):
        rollbar.report_message("Got cached news", level="info", request=request)
        return ret

    async with get_browser() as browser:
        ret = await gather_services(
            *[
                getattr(html, html_service_name)(browser)
                for html_service_name in html.__all__
            ]
        )

        background_tasks.add_task(set_cache, key, ret, redis=redis, settings=settings)
        rollbar.report_message("Got fresh news", level="info", request=request)

    return ret
