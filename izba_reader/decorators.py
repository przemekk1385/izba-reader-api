from functools import wraps

import rollbar


def async_report_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e_info:  # noqa
            rollbar.report_exc_info()
            raise

    return wrapper
