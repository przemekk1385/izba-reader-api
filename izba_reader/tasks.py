import asyncio

import httpx

from izba_reader.services import html, rss
from izba_reader.services.html import get_browser


async def fetch_rss_feeds():
    async with httpx.AsyncClient() as client:
        return await asyncio.gather(
            *[
                getattr(rss, rss_service_name)(client)
                for rss_service_name in rss.__all__
            ]
        )


async def scrap_web():
    async with get_browser() as browser:
        return await asyncio.gather(
            *[
                getattr(html, html_service_name)(browser)
                for html_service_name in html.__all__
            ]
        )
