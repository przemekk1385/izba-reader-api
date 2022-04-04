import asyncio
import itertools

import httpx

from izba_reader.services import html, rss
from izba_reader.services.html import get_browser


async def get_mail_text_body() -> str:
    feeds, news = (
        list(chain)
        for chain in (
            itertools.chain(*result)
            for result in await asyncio.gather(fetch_rss_feeds(), scrap_web())
        )
    )

    return "\n\n".join(
        [
            "\n\n".join(
                [
                    "source:RSS\n"
                    f"{item['title']}\n"
                    f"{item['description']}\n"
                    f"{item['link']}"
                    for item in feeds
                ]
                if feeds
                else ["no RSS items"]
            ),
            "\n\n".join(
                [
                    "source:WEB\n"
                    f"{item['date']}\n"
                    f"{item['title']}\n"
                    f"{item['description']}\n"
                    f"{item['link']}"
                    for item in news
                ]
                if news
                else ["no WEB items"]
            ),
        ]
    )


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
