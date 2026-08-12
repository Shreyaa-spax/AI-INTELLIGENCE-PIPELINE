import asyncio
import os
import aiohttp
import feedparser
import json
import re
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
        "url": "https://www.arbeitnow.com/api/job-board-api",
        "type": "api_json"
    },
    {
        "name": "Remotive",
        "url": "https://remotive.com/api/remote-jobs?category=software-development",
        "type": "api_json"
    },
    {
        "name": "We Work Remotely",
        "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "type": "rss"
    },
    {
        "name": "Python.org Jobs",
        "url": "https://www.python.org/jobs/feed/rss/",
        "type": "rss"
    },
    {
        "name": "Jobspresso",
        "url": "https://jobspresso.co/feed/",
        "type": "rss"
    }
]

# AI Keywords for filtering generic job listings
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning", 
    "ml", "data scientist", "data science", "nlp", "natural language",
    "computer vision", "llm", "neural network", "openai", "pytorch", "tensorflow"
]

def clean_company_name(name):
    if not name:
        return "Unknown"
    # Remove common extra words or clean spaces
    return name.strip()

def is_ai_job(title, description):
    text = f"{(title or '')} {(description or '')}".lower()
    for kw in AI_KEYWORDS:
        # Use word boundaries for short keywords like "ai" and "ml"
        if kw in ["ai", "ml"]:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return True
        else:
            if kw in text:
                return True
    return False

def parse_date(date_string):
    if not date_string:
        return None

    s = str(date_string).lower().strip()
    now = datetime.now(timezone.utc)
    
    # Handle relative dates
    if "ago" in s or "yesterday" in s:
        if "yesterday" in s:
            return now - timedelta(days=1)
        match = re.search(r"(\d+)\s*(hour|hr|h|minute|min|m|day|d)\b", s)
        if match:
            val = int(match.group(1))
            unit = match.group(2)
            if unit in ["hour", "hr", "h"]:
                return now - timedelta(hours=val)
            elif unit in ["minute", "min", "m"]:
                return now - timedelta(minutes=val)
            elif unit in ["day", "d"]:
                return now - timedelta(days=val)

    # Parse standard email parsed date (RFC 822)
    try:
        dt = parsedate_to_datetime(date_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # Parse ISO dates
    try:
        clean_ds = date_string.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_ds)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    return None

def is_fresh(date_string):
    published = parse_date(date_string)
    if not published:
        return False
    now = datetime.now(timezone.utc)
    age = now - published
    # Allow 24 hours plus a 2-hour buffer for scraping delays/timezone offsets
    return timedelta(seconds=0) <= age <= timedelta(hours=26)

async def fetch(session, url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with session.get(url, headers=headers, timeout=30) as response:
            print(f"Fetch {url} -> Status: {response.status}")
            if response.status != 200:
                return None
            return await response.text()
    except Exception as error:
        print(f"Request failed for {url}: {error}")
        return None

def parse_news_feed(source_name, source_url, xml_data):
    feed = feedparser.parse(xml_data)
    records = []
    seen_urls = set()

    for entry in feed.entries:
        published = entry.get("published") or entry.get("updated")
        if not published:
            continue

        if not is_fresh(published):
            continue

        title = entry.get("title", "").strip()
        url = entry.get("link", source_url).strip()
        summary = entry.get("summary", "").strip()
        # Clean HTML from summary
        summary = re.sub(r'<[^>]+>', '', summary)

        if url in seen_urls:
            continue
        seen_urls.add(url)

        normalized_pub_date = parse_date(published).isoformat()

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
                "published_date": normalized_pub_date
            },
            "collectedAt": datetime.now(timezone.utc).isoformat()
        })

    return records

async def crawl_news():
    print("\n===== NEWS CRAWLER =====")
    connector = aiohttp.TCPConnector(limit=5)
    all_news = []
    seen_urls = set()

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch(session, source["url"]) for source in NEWS_SOURCES]
        results = await asyncio.gather(*tasks)

        for source, xml_data in zip(NEWS_SOURCES, results):
            if not xml_data:
                continue

            try:
                records = parse_news_feed(source["name"], source["url"], xml_data)
                # Deduplicate overall news list
                for r in records:
                    url = r["source"]["url"]
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_news.append(r)
                print(f"{source['name']}: {len(records)} fresh articles")
            except Exception as e:
                print(f"Failed parsing news feed {source['name']}: {e}")

    return all_news

async def crawl_jobs():
    print("\n===== JOB CRAWLER =====")
    connector = aiohttp.TCPConnector(limit=5)
    all_jobs = []
    seen_urls = set()

    async with aiohttp.ClientSession(connector=connector) as session:
        for source in JOB_SOURCES:
            data = await fetch(session, source["url"])
            if not data:
                continue

            jobs_list = []
            if source["type"] == "api_json":
                try:
                    parsed_json = json.loads(data)
                    if source["name"] == "Arbeitnow":
                        jobs_list = parsed_json.get("data", [])
                    elif source["name"] == "Remotive":
                        jobs_list = parsed_json.get("jobs", [])
                except Exception as e:
                    print(f"JSON parse error for {source['name']}: {e}")
                    continue
            elif source["type"] == "rss":
                try:
                    feed = feedparser.parse(data)
                    jobs_list = feed.entries
                except Exception as e:
                    print(f"RSS parse error for {source['name']}: {e}")
                    continue

            source_count = 0
            for job in jobs_list:
                # 1. Extract raw values based on source structure
                title = ""
                company = ""
                url = ""
                description = ""
                date_str = ""
                is_remote = False

                if source["name"] == "Arbeitnow":
                    title = job.get("title", "")
                    company = job.get("company_name", "")
                    url = job.get("url", "")
                    description = job.get("description", "")
                    created = job.get("created_at")
                    if created:
                        date_str = datetime.fromtimestamp(created, timezone.utc).isoformat()
                    is_remote = job.get("remote", False)

                elif source["name"] == "Remotive":
                    title = job.get("title", "")
                    company = job.get("company_name", "")
                    url = job.get("url", "")
                    description = job.get("description", "")
                    date_str = job.get("publication_date", "")
                    is_remote = "remote" in str(job.get("candidate_required_location", "")).lower()

                elif source["name"] in ["We Work Remotely", "Python.org Jobs", "Jobspresso"]:
                    title = job.get("title", "")
                    url = job.get("link", "")
                    description = job.get("summary", "") or job.get("description", "")
                    date_str = job.get("published") or job.get("updated")
                    is_remote = True # RSS directories are largely remote-first or remote-friendly
                    
                    # Try to separate company name from title
                    # E.g. "Senior Python Engineer at OpenAI" or "Backend Developer, Google"
                    if " at " in title:
                        parts = title.split(" at ")
                        title = parts[0]
                        company = parts[1]
                    elif ", " in title:
                        parts = title.split(", ")
                        title = parts[0]
                        company = parts[1]
                    else:
                        company = source["name"]

                # 2. Check 24 hour freshness
                if not date_str or not is_fresh(date_str):
                    continue

                # 3. Keyword filter for AI jobs (except for Arbeitnow/Remotive, which we also filter for precision)
                if not is_ai_job(title, description):
                    continue

                # 4. Clean values and resolve types
                company = clean_company_name(company)
                url = url.strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                normalized_date = parse_date(date_str).isoformat()

                all_jobs.append({
                    "schemaVersion": "1.0",
                    "recordType": "JOB",
                    "source": {
                        "name": source["name"],
                        "url": url
                    },
                    "content": {
                        "company": company,
                        "date": normalized_date,
                        "is_remote": bool(is_remote),
                        "role_family": "Engineering"
                    },
                    "collectedAt": datetime.now(timezone.utc).isoformat()
                })
                source_count += 1

            print(f"{source['name']}: {source_count} fresh AI jobs found")

    return all_jobs

async def run_signal_pipeline():
    news = await crawl_news()
    jobs = await crawl_jobs()

    # Save outputs to data dir
    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as file:
        json.dump(news, file, indent=4, ensure_ascii=False)

    with open("data/jobs.json", "w", encoding="utf-8") as file:
        json.dump(jobs, file, indent=4, ensure_ascii=False)

    print(f"\nSaved Fresh news: {len(news)}")
    print(f"Saved Fresh jobs: {len(jobs)}")
    return news, jobs

if __name__ == "__main__":
    asyncio.run(run_signal_pipeline())