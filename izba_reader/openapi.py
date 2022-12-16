from fastapi.openapi.utils import get_openapi


def custom_openapi() -> dict:
    from izba_reader import __version__
    from izba_reader.main import app

    if app.openapi_schema:
        return app.openapi_schema

    return get_openapi(
        title="izba-reader API",
        version=__version__,
        routes=app.routes,
    )
