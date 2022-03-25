import asyncio
import itertools
from datetime import date, datetime

from bs4 import BeautifulSoup
from pyppeteer.browser import Browser

__all__ = ["scrap_cire_pl"]


async def _get_content(browser: Browser, url: str) -> str:
    page = await browser.newPage()
    await page.goto(url, {"waitUntil": ["domcontentloaded", "networkidle0"]})

    return await page.content()


async def scrap_cire_pl(browser: Browser) -> list[dict]:
    async def _scrap_cire_pl(p: int) -> list[dict]:
        soup = BeautifulSoup(
            await _get_content(
                browser,
                f"https://www.cire.pl/artykuly/energetyka?p={p}",
            ),
            features="html.parser",
        )

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

    return list(
        itertools.chain(
            *await asyncio.gather(
                _scrap_cire_pl(p=1),
                _scrap_cire_pl(p=2),
            )
        )
    )
