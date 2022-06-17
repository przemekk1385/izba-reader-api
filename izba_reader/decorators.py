import rollbar


def async_report_exceptions(func):
    async def _async_report_exceptions(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e_info:  # noqa
            rollbar.report_message(f"'{func.__name__}' has failed.", level="error")
            rollbar.report_exc_info()

    return _async_report_exceptions
