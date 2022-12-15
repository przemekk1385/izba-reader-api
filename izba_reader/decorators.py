from functools import wraps

from sentry_sdk import capture_exception


def capture_background_task_exception(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as exception:
            capture_exception(exception)
            raise

    return wrapper
