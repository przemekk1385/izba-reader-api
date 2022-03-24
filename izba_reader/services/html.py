import asyncio
import itertools
from datetime import date, datetime

from bs4 import BeautifulSoup
from pyppeteer import launch
from pyppeteer.browser import Browser


# TODO: base class etc.
class CirePl:
    browser: Browser = None

    def __init__(self, *args: str) -> None:
        self._urls = args

    async def __ainit__(self):
        self.browser = await launch()

    async def _fetch(self, url: str) -> str:
        page = await self.browser.newPage()
        await page.goto(url, {"waitUntil": ["domcontentloaded", "networkidle0"]})
        return await page.content()

    async def fetch(self):
        return list(
            itertools.chain(
                *[
                    self.parse(html)
                    for html in await asyncio.gather(
                        *[self._fetch(url) for url in self._urls]
                    )
                ]
            )
        )

    def parse(self, html):
        soup = BeautifulSoup(html, features="html.parser")
        hrefs = {
            tag["href"]
            for tag in soup.findAll(
                "a",
                href=lambda x: x
                and x.startswith("/artykuly/serwis-informacyjny-cire-24/"),
            )
        }

        news = []
        for tag in (soup.find("a", href=href) for href in hrefs):
            next_sibling = tag.next_sibling()
            news.append(
                {
                    "link": tag["href"],
                    "description": "\n".join(
                        next_sibling[i].text for i in range(3, len(next_sibling) - 1)
                    ),
                    "title": next_sibling[2].text,
                    "date": datetime.strptime(next_sibling[1].text, "%Y-%m-%d %H:%M"),
                }
            )

        news.sort(key=lambda x: x["date"], reverse=True)

        return [n for n in news if n["date"].date() == date.today()]


async def create_cire_pl():
    cire_pl_ = CirePl(
        "https://www.cire.pl/artykuly/energetyka?p=1",
        "https://www.cire.pl/artykuly/energetyka?p=2",
    )
    await cire_pl_.__ainit__()
    return cire_pl_
