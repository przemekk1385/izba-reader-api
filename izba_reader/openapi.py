from fastapi.openapi.utils import get_openapi


def custom_openapi():
    from izba_reader import app

    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="izba-reader API",
        version="0.2.0",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema
