from functools import wraps

from sentry_sdk import capture_exception as sentry_capture_exception


def capture_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exception:
            sentry_capture_exception(exception)
            raise

    return wrapper
