import asyncio

import httpx

from izba_reader.services import rss
from izba_reader.services.html import create_cire_pl


async def fetch_rss_feeds():
    async with httpx.AsyncClient() as client:
        return await asyncio.gather(
            *[
                getattr(rss, rss_service_name)(client)
                for rss_service_name in rss.__all__
            ]
        )


async def scrap_web():
    # TODO: tasks auto collecting
    cire_pl = await create_cire_pl()

    results = await asyncio.gather(cire_pl.fetch())
    return results
