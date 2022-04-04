from aioredis import Redis
from fastapi import BackgroundTasks, Depends

from izba_reader.services.cache import get_redis
from izba_reader.settings import Settings, get_settings
from izba_reader.tasks import get_both


async def make_text_body(
    background_tasks: BackgroundTasks,
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> str:
    feeds, news = await get_both(background_tasks, redis=redis, settings=settings)

    return "\n\n".join(
        [
            "\n\n".join(
                [
                    "#rss\n"
                    f"{item['title']}\n"
                    f"{item['description']}\n"
                    f"{item['link']}"
                    for item in feeds["items"]
                ]
                if feeds["items"]
                else ["no #rss"]
            ),
            "\n\n".join(
                [
                    "#web\n"
                    f"{item['date']}\n"
                    f"{item['title']}\n"
                    f"{item['description']}\n"
                    f"{item['link']}"
                    for item in news["items"]
                ]
                if news["items"]
                else ["no #web"]
            ),
        ]
    )
