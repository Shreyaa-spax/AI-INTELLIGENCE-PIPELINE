import asyncio
import aiohttp
import feedparser
import json
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime


NEWS_SOURCES = [
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/"
    },
    {
        "name": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/"
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/"
    },
    {
        "name": "The Decoder",
        "url": "https://the-decoder.com/feed/"
    },
    {
        "name": "MarkTechPost",
        "url": "https://www.marktechpost.com/feed/"
    }
]


JOB_SOURCES = [
    {
        "name": "Arbeitnow",
        "url": "https://www.arbeitnow.com/api/job-board-api"
    }
]


def parse_date(date_string):

    if not date_string:
        return None

    try:

        dt = parsedate_to_datetime(
            date_string
        )

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    except Exception:

        try:

            dt = datetime.fromisoformat(
                date_string.replace(
                    "Z",
                    "+00:00"
                )
            )

            return dt.astimezone(
                timezone.utc
            )

        except Exception:

            return None


def is_fresh(date_string):

    published = parse_date(
        date_string
    )

    if not published:
        return False

    now = datetime.now(
        timezone.utc
    )

    age = now - published

    return timedelta(
        seconds=0
    ) <= age <= timedelta(
        hours=24
    )


async def fetch(session, url):

    try:

        async with session.get(
            url,
            timeout=30
        ) as response:

            print(
                f"{url} -> {response.status}"
            )

            if response.status != 200:
                return None

            return await response.text()

    except Exception as error:

        print(
            f"Request failed: {error}"
        )

        return None


def parse_news_feed(
    source_name,
    source_url,
    xml_data
):

    feed = feedparser.parse(
        xml_data
    )

    records = []

    for entry in feed.entries:

        published = (
            entry.get("published")
            or entry.get("updated")
        )

        if not published:
            continue

        if not is_fresh(
            published
        ):
            continue

        title = entry.get(
            "title",
            ""
        )

        url = entry.get(
            "link",
            source_url
        )

        summary = entry.get(
            "summary",
            ""
        )

        records.append({

            "schemaVersion": "1.0",

            "recordType": "NEWS",

            "source": {
                "name": source_name,
                "url": url
            },

            "content": {
                "title": title,
                "text": summary,
                "published_date": published
            },

            "collectedAt":
                datetime.now(
                    timezone.utc
                ).isoformat()
        })

    return records


async def crawl_news():

    print(
        "\n===== NEWS CRAWLER ====="
    )

    connector = aiohttp.TCPConnector(
        limit=5
    )

    all_news = []

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        tasks = []

        for source in NEWS_SOURCES:

            tasks.append(
                fetch(
                    session,
                    source["url"]
                )
            )

        results = await asyncio.gather(
            *tasks
        )

        for source, xml_data in zip(
            NEWS_SOURCES,
            results
        ):

            if not xml_data:
                continue

            records = parse_news_feed(
                source["name"],
                source["url"],
                xml_data
            )

            print(
                f"{source['name']}: "
                f"{len(records)} fresh articles"
            )

            all_news.extend(
                records
            )

    return all_news


async def crawl_jobs():

    print(
        "\n===== JOB CRAWLER ====="
    )

    connector = aiohttp.TCPConnector(
        limit=5
    )

    all_jobs = []

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        for source in JOB_SOURCES:

            data = await fetch(
                session,
                source["url"]
            )

            if not data:
                continue

            try:

                jobs = json.loads(
                    data
                ).get(
                    "data",
                    []
                )

            except Exception:

                continue

            for job in jobs:

                created = job.get(
                    "created_at"
                )

                if not created:
                    continue

                date_string = (
                    datetime.fromtimestamp(
                        created,
                        timezone.utc
                    ).isoformat()
                )

                if not is_fresh(
                    date_string
                ):
                    continue

                all_jobs.append({

                    "schemaVersion": "1.0",

                    "recordType": "JOB",

                    "source": {
                        "name": source["name"],
                        "url": job.get(
                            "url"
                        )
                    },

                    "content": {

                        "company": job.get(
                            "company_name"
                        ),

                        "date": date_string,

                        "is_remote":
                            job.get(
                                "remote",
                                False
                            ),

                        "role_family":
                            "Engineering"
                    },

                    "collectedAt":
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                })

    return all_jobs


async def run_signal_pipeline():

    news = await crawl_news()

    jobs = await crawl_jobs()

    with open(
        "data/news.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            news,
            file,
            indent=4,
            ensure_ascii=False
        )

    with open(
        "data/jobs.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            jobs,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"\nFresh news: {len(news)}"
    )

    print(
        f"Fresh jobs: {len(jobs)}"
    )

    return news, jobs


if __name__ == "__main__":

    asyncio.run(
        run_signal_pipeline()
    )