import asyncio
import itertools
from datetime import datetime

from izba_reader import timezones


async def gather_services(*services):
    return {
        "items": list(itertools.chain(*await asyncio.gather(*services))),
        "time": datetime.now().astimezone(timezones.EUROPE_WARSAW),
    }
