from datetime import datetime
from typing import Callable

from bs4 import BeautifulSoup

DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def cire_pl(page: str) -> list[dict]:
    soup = BeautifulSoup(page, features="lxml")

    hrefs = {
        tag.attrs.get("href")
        for tag in soup.findAll(
            "a",
            href=lambda x: x and x.startswith("/artykuly/serwis-informacyjny-cire-24/"),
        )
    }

    ret = []
    for tag in (soup.find("a", href=href) for href in hrefs):
        assert callable(tag.next_sibling)

        next_sibling = tag.next_sibling()

        try:
            dt = datetime.strptime(next_sibling[1].text, DATETIME_FORMAT)
        except ValueError:
            dt = datetime.strptime(next_sibling[2].text, DATETIME_FORMAT)
            title = next_sibling[3].text
            description = "\n".join(
                next_sibling[i].text for i in range(4, len(next_sibling) - 1)
            )
        else:
            title = next_sibling[2].text
            description = "\n".join(
                next_sibling[i].text for i in range(3, len(next_sibling) - 1)
            )

        ret.append(
            {
                "title": title,
                "description": description
                if description.endswith(".")
                else f"{description} […]",
                "url": f"https://www.cire.pl{tag['href']}",
                "date": dt,
            }
        )

    ret.sort(key=lambda x: x["date"], reverse=True)
    return ret


def biznesalert_pl(feed: str) -> list[dict]:
    soup = BeautifulSoup(feed, features="xml")

    return [
        {
            "title": item.find("title").text,
            "description": BeautifulSoup(item.find("description").text)
            .findAll("p")[0]
            .text,
            "url": item.link.text,
        }
        for item in soup.findAll("item")
    ]


def wnp_pl(feed: str) -> list[dict]:
    soup = BeautifulSoup(feed, features="xml")

    return [
        {
            "title": item.find("title").text,
            "description": item.find("description").text,
            "url": item.link.text,
        }
        for item in soup.findAll("item")
    ]


def get_parser(host: str) -> Callable[[str], list[dict]]:
    return {
        "www.cire.pl": cire_pl,
        "biznesalert.pl": biznesalert_pl,
        "www.wnp.pl": wnp_pl,
    }.get(host, lambda _: list())
