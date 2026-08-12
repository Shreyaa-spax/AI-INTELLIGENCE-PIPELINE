import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone

# We use the unofficial public YC companies API feed
BASE_URL = "https://raw.githubusercontent.com/yc-oss/api/main/companies/all.json"

def make_startup_record(name, website, ycombinator_url, employee_count):
    # Use the company's website as the URL, fallback to YC URL if website is missing
    source_url = website if website else ycombinator_url
    
    # Try to parse employee count as an integer
    emp_count = None
    if employee_count is not None:
        try:
            emp_count = int(employee_count)
        except (ValueError, TypeError):
            emp_count = None

    return {
        "schemaVersion": "1.0",
        "recordType": "STARTUP",
        "source": {
            "name": "Y Combinator",
            "url": source_url
        },
        "content": {
            "entityName": name,
            "data": {
                "employeeCount": emp_count
            }
        },
        "collectedAt": datetime.now(timezone.utc).isoformat()
    }

async def scrape_startups():
    print("Starting startup scraper (YC OSS API)...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    connector = aiohttp.TCPConnector(limit=5)
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        try:
            async with session.get(BASE_URL, timeout=30) as response:
                print(f"Status: {response.status}")
                if response.status != 200:
                    print("Failed to download startups from YC API")
                    return []
                text_data = await response.text()
                startups_data = json.loads(text_data)
        except Exception as error:
            print("Scraping startups failed:", error)
            return []

    records = []
    seen = set()

    for item in startups_data:
        name = item.get("name")
        website = item.get("website")
        yc_url = item.get("url")
        tags = [t.lower() for t in item.get("tags", []) or []]
        industry = (item.get("industry") or "").lower()
        subindustry = (item.get("subindustry") or "").lower()
        one_liner = (item.get("one_liner") or "").lower()
        long_desc = (item.get("long_description") or "").lower()
        team_size = item.get("team_size")

        if not name:
            continue

        # Prioritize and filter for AI / ML / Data companies to populate the AI ecosystem pipeline
        is_ai = False
        if "artificial intelligence" in tags or "ai" in tags or "machine learning" in tags or "generative ai" in tags:
            is_ai = True
        elif "artificial intelligence" in industry or "machine learning" in industry:
            is_ai = True
        elif "artificial intelligence" in subindustry or "machine learning" in subindustry:
            is_ai = True
        elif " ai " in one_liner or "artificial intelligence" in one_liner or "machine learning" in one_liner:
            is_ai = True
        elif " ai " in long_desc or "artificial intelligence" in long_desc or "machine learning" in long_desc:
            is_ai = True

        if not is_ai:
            continue

        # Standardize company names for matching / deduping
        key = name.strip().lower()
        if key in seen:
            continue
        seen.add(key)

        record = make_startup_record(
            name=name.strip(),
            website=website,
            ycombinator_url=yc_url,
            employee_count=team_size
        )
        records.append(record)

    # We need >= 1000. Let's slice to a clean number (e.g. 1100) to ensure we satisfy requirements with a margin.
    print(f"Filtered {len(records)} AI startups out of {len(startups_data)} total YC startups.")
    return records[:1100]

async def main():
    records = await scrape_startups()
    os.makedirs("data", exist_ok=True)
    with open("data/startups.json", "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)
    print(f"Saved {len(records)} startup records to data/startups.json.")

if __name__ == "__main__":
    asyncio.run(main())