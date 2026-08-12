import asyncio
import os
import aiohttp
import feedparser
import json
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

NEWS_SOURCES = [
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "MIT Technology Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "The Decoder", "url": "https://the-decoder.com/feed/"},
    {"name": "MarkTechPost", "url": "https://www.marktechpost.com/feed/"}
]

JOB_SOURCES = [
    {"name": "Arbeitnow", "url": "https://www.arbeitnow.com/api/job-board-api", "type": "api_json"},
    {"name": "Remotive", "url": "https://remotive.com/api/remote-jobs?category=software-development", "type": "api_json"},
    {"name": "We Work Remotely", "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss", "type": "rss"},
    {"name": "Python.org Jobs", "url": "https://www.python.org/jobs/feed/rss/", "type": "rss"},
    {"name": "Jobspresso", "url": "https://jobspresso.co/feed/", "type": "rss"}
]

AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning", "ml",
    "data scientist", "data science", "nlp", "natural language", "computer vision",
    "llm", "neural network", "openai", "pytorch", "tensorflow"
]

def clean_company_name(name):
    return (name or "Unknown").strip()

def is_ai_job(title, description):
    text = f"{title or ''} {description or ''}".lower()
    for kw in AI_KEYWORDS:
        if kw in ("ai", "ml"):
            if re.search(r"\b" + re.escape(kw) + r"\b", text):
                return True
        elif kw in text:
            return True
    return False

def parse_date(date_string):
    if not date_string:
        return None
    s = str(date_string).lower().strip()
    now = datetime.now(timezone.utc)
    if "ago" in s or "yesterday" in s:
        if "yesterday" in s:
            return now - timedelta(days=1)
        match = re.search(r"(\d+)\s*(hour|hr|h|minute|min|m|day|d)\b", s)
        if match:
            val = int(match.group(1))
            unit = match.group(2)
            if unit in ["hour", "hr", "h"]:
                return now - timedelta(hours=val)
            if unit in ["minute", "min", "m"]:
                return now - timedelta(minutes=val)
            return now - timedelta(days=val)
    try:
        dt = parsedate_to_datetime(date_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(str(date_string).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def is_fresh(date_string):
    published = parse_date(date_string)
    if not published:
        return False
    age = datetime.now(timezone.utc) - published
    return timedelta(seconds=0) <= age <= timedelta(hours=24)

async def fetch(session, url):
    headers = {"User-Agent": "AI-Intelligence-Pipeline/1.0 (+https://github.com/Shreyaa-spax/AI-INTELLIGENCE-PIPELINE)"}
    try:
        async with session.get(url, headers=headers, timeout=30) as response:
            print(f"Fetch {url} -> Status: {response.status}")
            if response.status != 200:
                return None
            return await response.text()
    except Exception as error:
        print(f"Request failed for {url}: {error}")
        return None

async def fetch_article_text(session, url):
    """Best-effort full article extraction without fabricating text."""
    if not url:
        return ""
    try:
        from bs4 import BeautifulSoup
        html = await fetch(session, url)
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "nav", "header", "footer", "form"]):
            tag.decompose()
        candidates = soup.find_all(["article", "main"])
        if candidates:
            text = "\n".join(c.get_text(" ", strip=True) for c in candidates)
        else:
            paragraphs = soup.find_all("p")
            text = "\n".join(p.get_text(" ", strip=True) for p in paragraphs)
        return re.sub(r"\s+", " ", text).strip()
    except Exception as error:
        print(f"Article extraction failed for {url}: {error}")
        return ""

def parse_news_feed(source_name, source_url, xml_data):
    feed = feedparser.parse(xml_data)
    records = []
    for entry in feed.entries:
        published = entry.get("published") or entry.get("updated")
        if not published or not is_fresh(published):
            continue
        title = entry.get("title", "").strip()
        url = entry.get("link", source_url).strip()
        summary = re.sub(r"<[^>]+>", "", entry.get("summary", "").strip())
        records.append({
            "schemaVersion": "1.0",
            "recordType": "NEWS",
            "source": {"name": source_name, "url": url},
            "content": {"title": title, "text": summary, "published_date": parse_date(published).isoformat()},
            "collectedAt": datetime.now(timezone.utc).isoformat()
        })
    return records

async def crawl_news():
    print("\n===== NEWS CRAWLER =====")
    connector = aiohttp.TCPConnector(limit=5)
    all_news = []
    seen_urls = set()
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await asyncio.gather(*(fetch(session, s["url"]) for s in NEWS_SOURCES))
        for source, xml_data in zip(NEWS_SOURCES, results):
            if not xml_data:
                continue
            try:
                records = parse_news_feed(source["name"], source["url"], xml_data)
                for record in records:
                    url = record["source"]["url"]
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    full_text = await fetch_article_text(session, url)
                    if full_text:
                        record["content"]["text"] = full_text
                    all_news.append(record)
                print(f"{source['name']}: {len(records)} fresh articles")
            except Exception as error:
                print(f"Failed parsing news feed {source['name']}: {error}")
    return all_news

async def crawl_jobs():
    print("\n===== JOB CRAWLER =====")
    connector = aiohttp.TCPConnector(limit=5)
    all_jobs, seen_urls = [], set()
    async with aiohttp.ClientSession(connector=connector) as session:
        for source in JOB_SOURCES:
            data = await fetch(session, source["url"])
            if not data:
                continue
            if source["type"] == "api_json":
                try:
                    parsed = json.loads(data)
                    jobs_list = parsed.get("data", []) if source["name"] == "Arbeitnow" else parsed.get("jobs", [])
                except Exception as error:
                    print(f"JSON parse error for {source['name']}: {error}")
                    continue
            else:
                try:
                    jobs_list = feedparser.parse(data).entries
                except Exception as error:
                    print(f"RSS parse error for {source['name']}: {error}")
                    continue
            source_count = 0
            for job in jobs_list:
                title = company = url = description = date_str = ""
                is_remote = False
                if source["name"] == "Arbeitnow":
                    title, company, url, description = job.get("title", ""), job.get("company_name", ""), job.get("url", ""), job.get("description", "")
                    created = job.get("created_at")
                    date_str = datetime.fromtimestamp(created, timezone.utc).isoformat() if created else ""
                    is_remote = bool(job.get("remote", False))
                elif source["name"] == "Remotive":
                    title, company, url, description = job.get("title", ""), job.get("company_name", ""), job.get("url", ""), job.get("description", "")
                    date_str = job.get("publication_date", "")
                    is_remote = "remote" in str(job.get("candidate_required_location", "")).lower()
                else:
                    title = job.get("title", "")
                    url = job.get("link", "")
                    description = job.get("summary", "") or job.get("description", "")
                    date_str = job.get("published") or job.get("updated")
                    is_remote = True
                    if " at " in title:
                        title, company = title.split(" at ", 1)
                    elif ", " in title:
                        title, company = title.split(", ", 1)
                    else:
                        company = source["name"]
                if not date_str or not is_fresh(date_str) or not is_ai_job(title, description):
                    continue
                url = url.strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                all_jobs.append({
                    "schemaVersion": "1.0", "recordType": "JOB",
                    "source": {"name": source["name"], "url": url},
                    "content": {"company": clean_company_name(company), "date": parse_date(date_str).isoformat(), "is_remote": bool(is_remote), "role_family": "Engineering"},
                    "collectedAt": datetime.now(timezone.utc).isoformat()
                })
                source_count += 1
            print(f"{source['name']}: {source_count} fresh AI jobs found")
    return all_jobs

async def run_signal_pipeline():
    news = await crawl_news()
    jobs = await crawl_jobs()
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
