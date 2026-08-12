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

# Five currently usable public job feeds/APIs. Remotive's current category slug is software-dev;
# We Work Remotely publishes a public programming RSS feed; Remote OK and Remote First Jobs
# provide public RSS feeds suitable for aggregation.
JOB_SOURCES = [
    {"name": "Arbeitnow", "url": "https://www.arbeitnow.com/api/job-board-api", "type": "api_json"},
    {"name": "Remotive", "url": "https://remotive.com/api/remote-jobs?category=software-dev", "type": "api_json"},
    {"name": "We Work Remotely", "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss", "type": "rss"},
    {"name": "Remote OK", "url": "https://remoteok.com/remote-jobs.rss", "type": "rss"},
    {"name": "Remote First Jobs AI", "url": "https://remotefirstjobs.com/rss/jobs/ai.rss", "type": "rss"}
]

AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning", "ml",
    "data scientist", "data science", "nlp", "natural language", "computer vision",
    "llm", "neural network", "openai", "pytorch", "tensorflow", "generative ai",
    "genai", "mlops", "robotics", "agentic", "ai engineer", "machine learning engineer"
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
    for parser in (
        lambda value: parsedate_to_datetime(value),
        lambda value: datetime.fromisoformat(str(value).replace("Z", "+00:00")),
    ):
        try:
            dt = parser(date_string)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def is_fresh(date_string):
    published = parse_date(date_string)
    if not published:
        return False
    age = datetime.now(timezone.utc) - published
    return timedelta(seconds=0) <= age <= timedelta(hours=24)


async def fetch(session, url):
    headers = {
        "User-Agent": "AI-Intelligence-Pipeline/1.0 (+https://github.com/Shreyaa-spax/AI-INTELLIGENCE-PIPELINE)",
        "Accept": "application/rss+xml, application/xml, application/json, text/html;q=0.9, */*;q=0.8",
    }
    try:
        async with session.get(url, headers=headers, timeout=30, allow_redirects=True) as response:
            print(f"Fetch {url} -> Status: {response.status}")
            if response.status != 200:
                return None
            return await response.text()
    except Exception as error:
        print(f"Request failed for {url}: {error}")
        return None


async def fetch_article_text(session, url):
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
            text = "\n".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
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
            "schemaVersion": "1.0", "recordType": "NEWS",
            "source": {"name": source_name, "url": url},
            "content": {"title": title, "text": summary, "published_date": parse_date(published).isoformat()},
            "collectedAt": datetime.now(timezone.utc).isoformat()
        })
    return records


async def crawl_news():
    print("\n===== NEWS CRAWLER =====")
    connector = aiohttp.TCPConnector(limit=5)
    all_news, seen_urls, source_report = [], set(), {}
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await asyncio.gather(*(fetch(session, s["url"]) for s in NEWS_SOURCES))
        for source, xml_data in zip(NEWS_SOURCES, results):
            report = {"status": "FETCH_FAILED", "fresh": 0, "duplicates_removed": 0}
            if not xml_data:
                source_report[source["name"]] = report
                continue
            try:
                records = parse_news_feed(source["name"], source["url"], xml_data)
                report["status"], report["fresh"] = "OK", len(records)
                for record in records:
                    url = record["source"]["url"]
                    if url in seen_urls:
                        report["duplicates_removed"] += 1
                        continue
                    seen_urls.add(url)
                    full_text = await fetch_article_text(session, url)
                    if full_text:
                        record["content"]["text"] = full_text
                    all_news.append(record)
                source_report[source["name"]] = report
                print(f"{source['name']}: fresh={report['fresh']} duplicates={report['duplicates_removed']}")
            except Exception as error:
                report["status"] = f"PARSE_FAILED: {error}"
                source_report[source["name"]] = report
    return all_news, source_report


def job_fingerprint(company, title, url):
    if url:
        return "url:" + url.strip().lower().rstrip("/")
    return "job:" + re.sub(r"\W+", " ", f"{company} {title}").strip().lower()


def extract_jobs_for_source(source, data):
    if source["type"] == "api_json":
        parsed = json.loads(data)
        return parsed.get("data", []) if source["name"] == "Arbeitnow" else parsed.get("jobs", [])
    return feedparser.parse(data).entries


def normalize_job(source, job):
    title = company = url = description = date_str = ""
    is_remote = True
    if source["name"] == "Arbeitnow":
        title, company, url, description = job.get("title", ""), job.get("company_name", ""), job.get("url", ""), job.get("description", "")
        created = job.get("created_at")
        date_str = datetime.fromtimestamp(created, timezone.utc).isoformat() if created else ""
        is_remote = bool(job.get("remote", False))
    elif source["name"] == "Remotive":
        title, company, url, description = job.get("title", ""), job.get("company_name", ""), job.get("url", ""), job.get("description", "")
        date_str = job.get("publication_date", "")
        location = str(job.get("candidate_required_location", ""))
        is_remote = "remote" in location.lower() or location.lower() in {"anywhere", "worldwide"}
    else:
        title = job.get("title", "")
        url = job.get("link", "")
        description = job.get("summary", "") or job.get("description", "")
        date_str = job.get("published") or job.get("updated")
        # Most RSS feeds put company in the title. Keep the original title if no separator exists.
        if " at " in title:
            title, company = title.split(" at ", 1)
        elif ", " in title:
            title, company = title.split(", ", 1)
        else:
            company = source["name"]
        if source["name"] == "Remote OK":
            is_remote = True
    return title.strip(), clean_company_name(company), url.strip(), description, date_str, is_remote


async def crawl_jobs():
    print("\n===== JOB CRAWLER =====")
    connector = aiohttp.TCPConnector(limit=5)
    all_jobs, seen_fingerprints, source_report = [], set(), {}
    async with aiohttp.ClientSession(connector=connector) as session:
        for source in JOB_SOURCES:
            report = {"status": "FETCH_FAILED", "fresh": 0, "ai": 0, "unique": 0, "duplicates_removed": 0}
            data = await fetch(session, source["url"])
            if not data:
                source_report[source["name"]] = report
                continue
            try:
                jobs_list = extract_jobs_for_source(source, data)
                report["status"] = "OK"
                for job in jobs_list:
                    title, company, url, description, date_str, is_remote = normalize_job(source, job)
                    if not date_str or not is_fresh(date_str):
                        continue
                    report["fresh"] += 1
                    if not is_ai_job(title, description):
                        continue
                    report["ai"] += 1
                    fingerprint = job_fingerprint(company, title, url)
                    if fingerprint in seen_fingerprints:
                        report["duplicates_removed"] += 1
                        continue
                    parsed_date = parse_date(date_str)
                    if not parsed_date or not url:
                        continue
                    seen_fingerprints.add(fingerprint)
                    all_jobs.append({
                        "schemaVersion": "1.0", "recordType": "JOB",
                        "source": {"name": source["name"], "url": url},
                        "content": {"title": title, "company": company, "date": parsed_date.isoformat(), "is_remote": bool(is_remote), "role_family": "Engineering"},
                        "collectedAt": datetime.now(timezone.utc).isoformat()
                    })
                    report["unique"] += 1
                source_report[source["name"]] = report
                print(f"{source['name']}: fresh={report['fresh']} ai={report['ai']} unique={report['unique']} duplicates={report['duplicates_removed']}")
            except Exception as error:
                report["status"] = f"PARSE_FAILED: {error}"
                source_report[source["name"]] = report
                print(f"{source['name']}: {report['status']}")
    return all_jobs, source_report


async def run_signal_pipeline():
    news, news_report = await crawl_news()
    jobs, jobs_report = await crawl_jobs()
    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as file:
        json.dump(news, file, indent=4, ensure_ascii=False)
    with open("data/jobs.json", "w", encoding="utf-8") as file:
        json.dump(jobs, file, indent=4, ensure_ascii=False)
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(), "freshnessWindowHours": 24,
        "news": {"total_unique": len(news), "source_count": len(NEWS_SOURCES), "sources": news_report, "sources_with_fresh_records": sum(1 for v in news_report.values() if v.get("fresh", 0) > 0)},
        "jobs": {"total_unique": len(jobs), "source_count": len(JOB_SOURCES), "sources": jobs_report, "sources_with_fresh_ai_records": sum(1 for v in jobs_report.values() if v.get("unique", 0) > 0)},
        "validation": {"strict_24_hour_filter": True, "job_duplicates_removed": True, "news_duplicates_removed": True, "no_records_are_synthesized": True}
    }
    with open("data/signal_source_report.json", "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)
    print("\n===== SOURCE COVERAGE REPORT =====")
    print(f"News: {len(news)} unique | {report['news']['sources_with_fresh_records']}/{len(NEWS_SOURCES)} sources produced fresh records")
    print(f"Jobs: {len(jobs)} unique | {report['jobs']['sources_with_fresh_ai_records']}/{len(JOB_SOURCES)} sources produced fresh AI records")
    print("Report saved to data/signal_source_report.json")
    return news, jobs


if __name__ == "__main__":
    asyncio.run(run_signal_pipeline())
