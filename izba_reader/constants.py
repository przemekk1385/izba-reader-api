from pathlib import Path

from pydantic import BaseModel, HttpUrl


class Site(BaseModel):
    url: HttpUrl
    use_browser: bool


BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

SITES = [
    Site(url="https://biznesalert.pl/category/energetyka/feed/", use_browser=False),
    Site(
        url="http://www.wnp.pl/rss/serwis_rss_1.xml/",
        use_browser=False,
    ),
    Site(
        url="http://www.cire.pl/artykuly/energetyka?p=1",
        use_browser=True,
    ),
    Site(
        url="http://www.cire.pl/artykuly/energetyka?p=2",
        use_browser=True,
    ),
    Site(
        url="https://businessinsider.com.pl/gospodarka",
        use_browser=False,
    ),
    Site(
        url="https://businessinsider.com.pl/gospodarka?page=2",
        use_browser=False,
    ),
    Site(
        url="https://businessinsider.com.pl/biznes",
        use_browser=False,
    ),
    Site(
        url="https://businessinsider.com.pl/biznes?page=2",
        use_browser=False,
    ),
]
