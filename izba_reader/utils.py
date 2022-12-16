import os
from datetime import date, timedelta
from functools import lru_cache


@lru_cache
def get_border_date() -> date:
    today = date.today()
    days = {
        0: 4,
        5: 2,
        6: 3,
    }.get(today.weekday(), 1)
    return today - timedelta(days=days)


def get_env(name: str) -> str:
    return os.environ.get(name) or os.environ.get(f"APP_{name}")
