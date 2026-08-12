import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timezone


# Example public directory
BASE_URL = "https://www.futurepedia.io"


def make_startup_record(name, url):

    return {
        "schemaVersion": "1.0",
        "recordType": "STARTUP",
        "source": {
            "name": "Futurepedia",
            "url": url
        },
        "content": {
            "entityName": name,
            "data": {
                "employeeCount": None
            }
        },
        "collectedAt": datetime.now(
            timezone.utc
        ).isoformat()
    }


async def scrape_startups():

    print("Starting startup scraper...")

    headers = {
        "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/151.0 Safari/537.36"
    }

    async with aiohttp.ClientSession(
        headers=headers
    ) as session:

        try:

            async with session.get(
                BASE_URL,
                timeout=30
            ) as response:

                print(
                    "Status:",
                    response.status
                )

                html = await response.text()

        except Exception as error:

            print(
                "Scraping failed:",
                error
            )

            return []

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    records = []

    seen = set()

    for link in soup.find_all("a"):

        name = link.get_text(
            strip=True
        )

        href = link.get("href")

        if not name or not href:
            continue

        if len(name) < 2:
            continue

        if href.startswith("/"):

            href = BASE_URL + href

        if not href.startswith("http"):
            continue

        key = name.lower()

        if key in seen:
            continue

        seen.add(key)

        records.append(
            make_startup_record(
                name,
                href
            )
        )

    print(
        f"Found {len(records)} possible records."
    )

    return records


async def main():

    records = await scrape_startups()

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        "data/startups.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Saved {len(records)} startup records."
    )


if __name__ == "__main__":

    asyncio.run(main())