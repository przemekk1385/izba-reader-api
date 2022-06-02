import rollbar


def async_report_exceptions(func):
    async def _async_report_exceptions(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except:  # noqa
            rollbar.report_exc_info()

    return _async_report_exceptions
