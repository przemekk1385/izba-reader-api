from functools import partial
from http import HTTPStatus

from bs4 import BeautifulSoup
from httpx import AsyncClient

__all__ = ["get_biznesalert_pl", "get_wnp_pl"]

BeautifulSoup_ = partial(BeautifulSoup, features="html.parser")


async def get_biznesalert_pl(client: AsyncClient) -> list[dict]:
    response = await client.get("https://biznesalert.pl/category/energetyka/feed/")
    soup = BeautifulSoup_(response.text)
    return (
        [
            {
                "title": item.find("title").text,
                "description": BeautifulSoup_(item.find("description").text)
                .findAll("p")[0]
                .text,
                "link": item.link.next_sibling.strip(),
            }
            for item in soup.findAll("item")
        ]
        if response.status_code == HTTPStatus.OK
        else []
    )


async def get_wnp_pl(client: AsyncClient) -> list[dict]:
    response = await client.get(
        "http://www.wnp.pl/rss/serwis_rss_1.xml/", follow_redirects=True
    )
    soup = BeautifulSoup_(response.text)
    return (
        [
            {
                "title": item.find("title").text,
                "description": item.find("description").text,
                "link": item.link.next_sibling.strip(),
            }
            for item in soup.findAll("item")
        ]
        if response.status_code == HTTPStatus.OK
        else []
    )
