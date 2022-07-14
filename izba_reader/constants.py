from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

FEED_URLS = [
    "https://biznesalert.pl/category/energetyka/feed/",
    "http://www.wnp.pl/rss/serwis_rss_1.xml/",
]
NEWS_URLS = [
    "http://www.cire.pl/artykuly/energetyka?p=1",
    "http://www.cire.pl/artykuly/energetyka?p=2",
]

ORIGINS = [
    "http://127.0.0.1:8080",
    "http://localhost:8080",
]
