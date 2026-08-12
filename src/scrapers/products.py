import asyncio
import aiohttp
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime, timezone


URL = "https://www.futurepedia.io"


def make_product_record(name, url):

    return {
        "schemaVersion": "1.0",
        "recordType": "PRODUCT",
        "source": {
            "name": "Futurepedia",
            "url": url
        },
        "content": {
            "startupName": None,
            "pricingModel": "FREE"
        },
        "collectedAt": datetime.now(
            timezone.utc
        ).isoformat()
    }


async def scrape_products():

    print("Starting product scraper...")

    headers = {
        "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/151.0 Safari/537.36"
    }

    timeout = aiohttp.ClientTimeout(
        total=30
    )

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout
    ) as session:

        try:

            async with session.get(
                URL
            ) as response:

                print(
                    "Status:",
                    response.status
                )

                html = await response.text()

        except Exception as error:

            print(
                "Request failed:",
                error
            )

            return []

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    products = []
    seen_urls = set()

    # Only consider links that appear
    # to point to actual tool/product pages.
    for link in soup.find_all("a"):

        name = link.get_text(
            strip=True
        )

        href = link.get("href")

        if not name or not href:
            continue

        if href.startswith("/"):

            href = URL.rstrip("/") + href

        if not href.startswith("http"):
            continue

        # Ignore obvious navigation links
        ignored = {
            "home",
            "about",
            "pricing",
            "login",
            "sign up",
            "contact",
            "blog"
        }

        if name.lower() in ignored:
            continue

        if href in seen_urls:
            continue

        seen_urls.add(href)

        products.append(
            make_product_record(
                name,
                href
            )
        )

    return products


async def main():

    products = await scrape_products()

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        "data/products.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            products,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Saved {len(products)} products."
    )


if __name__ == "__main__":

    asyncio.run(main())