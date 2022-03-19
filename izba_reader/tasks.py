import asyncio

import httpx

from izba_reader.services import rss


async def fetch_rss_task():
    async with httpx.AsyncClient() as client:
        return await asyncio.gather(
            *[
                getattr(rss, rss_service_name)(client)
                for rss_service_name in rss.__all__
            ]
        )
