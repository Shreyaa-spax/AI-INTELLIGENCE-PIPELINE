import os
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
import json
import ssl
from datetime import datetime, timezone

from github_matcher import enrich_papers


ARXIV_URL = "https://export.arxiv.org/api/query"


# --------------------------------------------------
# Save papers
# --------------------------------------------------

def save_papers(papers):

    os.makedirs("data", exist_ok=True)

    with open(
        "data/research_papers.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            papers,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Saved {len(papers)} papers to "
        f"data/research_papers.json"
    )


# --------------------------------------------------
# Fetch ONE batch of papers
# --------------------------------------------------

async def fetch_papers(
    session,
    start=0,
    max_results=100
):

    params = {
        "search_query": "cat:cs.AI",
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    async with session.get(
        ARXIV_URL,
        params=params,
        timeout=60
    ) as response:

        print(
            f"ArXiv batch {start + 1}-"
            f"{start + max_results} | "
            f"Status: {response.status}"
        )

        xml_data = await response.text()

    root = ET.fromstring(xml_data)

    namespace = {
        "atom": "http://www.w3.org/2005/Atom"
    }

    papers = []

    for entry in root.findall(
        "atom:entry",
        namespace
    ):

        title = entry.find(
            "atom:title",
            namespace
        )

        published = entry.find(
            "atom:published",
            namespace
        )

        summary = entry.find(
            "atom:summary",
            namespace
        )

        paper_id = entry.find(
            "atom:id",
            namespace
        )

        authors = []

        for author in entry.findall(
            "atom:author",
            namespace
        ):

            name = author.find(
                "atom:name",
                namespace
            )

            if name is not None and name.text:
                authors.append(
                    name.text.strip()
                )

        if title is None or not title.text:
            continue

        paper_url = (
            paper_id.text.strip()
            if paper_id is not None
            else None
        )

        paper = {

            "schemaVersion": "1.0",

            "recordType": "RESEARCH_PAPER",

            "source": {
                "name": "ArXiv",
                "url": paper_url
            },

            "content": {

                "title": title.text.strip(),

                "authors": authors,

                "paper_url": paper_url,

                "github_url": None,

                "github_stars": None,

                "published_date": (
                    published.text.strip()
                    if published is not None
                    and published.text
                    else None
                ),

                "summary": (
                    summary.text.strip()
                    if summary is not None
                    and summary.text
                    else None
                )
            },

            "collectedAt":
                datetime.now(
                    timezone.utc
                ).isoformat()
        }

        papers.append(paper)

    return papers


# --------------------------------------------------
# Fetch 1,000 papers using pagination
# --------------------------------------------------

async def collect_papers(
    total=1000,
    batch_size=100
):

    all_papers = []

    # Fix Windows certificate issue
    ssl_context = ssl.create_default_context()

    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    connector = aiohttp.TCPConnector(
        ssl=ssl_context
    )

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        for start in range(
            0,
            total,
            batch_size
        ):

            print(
                "\nDownloading papers "
                f"{start + 1}-"
                f"{min(start + batch_size, total)}"
            )

            try:

                papers = await fetch_papers(
                    session=session,
                    start=start,
                    max_results=batch_size
                )

            except Exception as error:

                print(
                    f"ArXiv request failed: {error}"
                )

                continue

            all_papers.extend(papers)

            print(
                f"Collected so far: "
                f"{len(all_papers)}"
            )

            # If ArXiv returns fewer papers,
            # we have reached the end.
            if len(papers) < batch_size:
                break

            # Small delay between ArXiv requests
            await asyncio.sleep(2)

    return all_papers[:total]


# --------------------------------------------------
# Main paper pipeline
# --------------------------------------------------

async def run_paper_pipeline():

    print("=" * 60)
    print("STARTING ARXIV PAPER PIPELINE")
    print("=" * 60)

    # ----------------------------------------------
    # STEP 1: Collect papers
    # ----------------------------------------------

    papers = await collect_papers(
        total=1000,
        batch_size=100
    )

    print(
        f"\nCollected {len(papers)} papers."
    )

    # ----------------------------------------------
    # STEP 2: Save raw papers
    # ----------------------------------------------

    save_papers(papers)

    # ----------------------------------------------
    # STEP 3: GitHub enrichment
    # ----------------------------------------------

    print(
        "\nFinding GitHub repositories..."
    )

    papers = await enrich_papers(
        papers
    )

    # ----------------------------------------------
    # STEP 4: Save enriched papers
    # ----------------------------------------------

    save_papers(papers)

    # Also save a second copy
    with open(
        "data/papers.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            papers,
            file,
            indent=4,
            ensure_ascii=False
        )

    # ----------------------------------------------
    # STEP 5: Count GitHub repositories
    # ----------------------------------------------

    github_count = sum(
        1
        for paper in papers
        if paper["content"].get(
            "github_url"
        )
    )

    print("\n" + "=" * 60)

    print(
        f"Saved {len(papers)} papers."
    )

    print(
        f"GitHub repositories found: "
        f"{github_count}"
    )

    print("=" * 60)

    return papers


# --------------------------------------------------
# Run directly
# --------------------------------------------------

if __name__ == "__main__":

    asyncio.run(
        run_paper_pipeline()
    )