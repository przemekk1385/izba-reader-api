from contextlib import asynccontextmanager

import rollbar
from pyppeteer import launch
from pyppeteer.browser import Browser


@asynccontextmanager
async def launch_browser() -> Browser:
    browser = None
    try:
        browser = await launch(options={"args": ["--no-sandbox"]})
        yield browser
    except:  # noqa
        rollbar.report_exc_info()
    finally:
        browser and await browser.close()
