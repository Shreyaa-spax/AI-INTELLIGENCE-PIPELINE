import aiohttp
import asyncio
import os
import re
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITHUB_API = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


async def github_request(
    session,
    url,
    params=None,
    max_retries=4
):
    """
    GitHub request with retry and exponential backoff.
    """

    for attempt in range(max_retries):

        try:

            async with session.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=30
            ) as response:

                # Success
                if response.status == 200:

                    return await response.json()

                # Rate limit
                if response.status == 429:

                    retry_after = response.headers.get(
                        "Retry-After"
                    )

                    if retry_after:
                        wait = int(retry_after)
                    else:
                        wait = 2 ** attempt

                    print(
                        f"GitHub 429. "
                        f"Waiting {wait}s..."
                    )

                    await asyncio.sleep(wait)

                    continue

                # Forbidden / rate limit
                if response.status == 403:

                    remaining = response.headers.get(
                        "X-RateLimit-Remaining"
                    )

                    reset = response.headers.get(
                        "X-RateLimit-Reset"
                    )

                    print(
                        f"GitHub 403 "
                        f"(remaining={remaining})"
                    )

                    # If rate limit is exhausted,
                    # wait until GitHub reset time.

                    if remaining == "0" and reset:

                        import time

                        wait = max(
                            int(reset) - int(time.time()),
                            1
                        )

                        print(
                            f"Rate limit exhausted. "
                            f"Waiting {wait}s..."
                        )

                        await asyncio.sleep(
                            wait
                        )

                    else:

                        wait = 2 ** attempt

                        await asyncio.sleep(
                            wait
                        )

                    continue

                print(
                    f"GitHub HTTP error: "
                    f"{response.status}"
                )

                return None

        except Exception as error:

            wait = 2 ** attempt

            print(
                f"GitHub connection error: "
                f"{error}"
            )

            print(
                f"Retrying in {wait}s..."
            )

            await asyncio.sleep(wait)

    print(
        "GitHub request failed after "
        f"{max_retries} attempts."
    )

    return None


def extract_github_url(text):

    if not text:
        return None

    pattern = (
        r"https?://github\.com/"
        r"[A-Za-z0-9_.-]+/"
        r"[A-Za-z0-9_.-]+"
    )

    match = re.search(
        pattern,
        text
    )

    if match:
        return match.group(0).rstrip(
            ".,)"
        )

    return None


async def get_github_stars(
    session,
    github_url
):

    if not github_url:
        return None

    match = re.search(
        r"github\.com/([^/]+)/([^/]+)",
        github_url
    )

    if not match:
        return None

    owner = match.group(1)
    repo = match.group(2)

    url = (
        f"{GITHUB_API}/repos/"
        f"{owner}/{repo}"
    )

    data = await github_request(
        session,
        url
    )

    if not data:
        return None

    return data.get(
        "stargazers_count"
    )


async def search_github(
    session,
    title
):

    if not title:
        return None

    url = (
        f"{GITHUB_API}/search/repositories"
    )

    params = {
        "q": title,
        "per_page": 5
    }

    data = await github_request(
        session,
        url,
        params=params
    )

    if not data:
        return None

    items = data.get(
        "items",
        []
    )

    if not items:
        return None

    return items[0].get(
        "html_url"
    )


async def enrich_paper(
    session,
    paper
):

    content = paper.get(
        "content",
        {}
    )

    title = content.get(
        "title"
    )

    summary = content.get(
        "summary"
    )

    github_url = extract_github_url(
        f"{title} {summary}"
    )

    if not github_url:

        github_url = await search_github(
            session,
            title
        )

    stars = None

    if github_url:

        stars = await get_github_stars(
            session,
            github_url
        )

    content["github_url"] = github_url

    content["github_stars"] = stars

    return paper


async def enrich_papers(papers):

    connector = aiohttp.TCPConnector(
        limit=5
    )

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        results = []

        for index, paper in enumerate(
            papers,
            start=1
        ):

            print(
                f"[{index}/{len(papers)}] "
                f"{paper['content']['title'][:60]}"
            )

            enriched = await enrich_paper(
                session,
                paper
            )

            results.append(
                enriched
            )

            # Prevent aggressive requests
            await asyncio.sleep(0.5)

    return results