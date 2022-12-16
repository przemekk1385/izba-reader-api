from fastapi.openapi.utils import get_openapi


def custom_openapi():
    from izba_reader import __version__, app

    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="izba-reader API",
        version=__version__,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema
