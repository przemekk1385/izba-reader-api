from pathlib import Path

from pydantic import HttpUrl, parse_obj_as


class BrowsableUrl(HttpUrl):
    pass


BASE_DIR = Path(__file__).resolve().parent.parent

FALLBACK_ARTICLES_COUNT = 3

URLS = [
    parse_obj_as(HttpUrl, "https://biznesalert.pl/category/energetyka/feed/"),
    parse_obj_as(HttpUrl, "http://www.wnp.pl/rss/serwis_rss_1.xml/"),
    parse_obj_as(HttpUrl, "https://businessinsider.com.pl/gospodarka"),
    parse_obj_as(HttpUrl, "https://businessinsider.com.pl/gospodarka?page=2"),
    parse_obj_as(HttpUrl, "https://businessinsider.com.pl/biznes"),
    parse_obj_as(HttpUrl, "https://businessinsider.com.pl/biznes?page=2"),
    parse_obj_as(HttpUrl, "https://wysokienapiecie.pl/kategoria/oze/"),
    parse_obj_as(HttpUrl, "https://wysokienapiecie.pl/kategoria/klimat/"),
    parse_obj_as(
        HttpUrl, "https://wysokienapiecie.pl/kategoria/energetyka-konwencjonalna/"
    ),
    parse_obj_as(BrowsableUrl, "http://www.cire.pl/artykuly/energetyka?p=1"),
    parse_obj_as(BrowsableUrl, "http://www.cire.pl/artykuly/energetyka?p=2"),
]
