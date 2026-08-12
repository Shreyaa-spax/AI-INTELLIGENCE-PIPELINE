import asyncio
import os
import sys

# Ensure project root and src directory are in Python path
sys.path.append(os.path.dirname(__file__))

from scrapers.papers import run_paper_pipeline
from scrapers.startups import scrape_startups
from scrapers.products import scrape_products
from signals.crawler import run_signal_pipeline
from resolver.apply_resolver import main as run_entity_resolution
from export import main as run_csv_export

async def main():
    print("=" * 60)
    print("AI INTELLIGENCE PIPELINE ORCHESTRATOR")
    print("=" * 60)

    # 1. Scrape Startups
    print("\n[1] Scraping Startups...")
    startups = await scrape_startups()
    os.makedirs("data", exist_ok=True)
    with open("data/startups.json", "w", encoding="utf-8") as f:
        import json
        json.dump(startups, f, indent=2, ensure_ascii=False)
    print(f"Startups collected: {len(startups)}")

    # 2. Scrape Products
    print("\n[2] Scraping Products...")
    products = await scrape_products()
    with open("data/products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"Products collected: {len(products)}")

    # 3. Scrape Research Papers
    print("\n[3] Ingesting Research Papers...")
    papers = await run_paper_pipeline()
    print(f"Research papers processed: {len(papers)}")

    # 4. Ingest Jobs & News
    print("\n[4] Crawling Jobs & News (last 24 hours)...")
    news, jobs = await run_signal_pipeline()
    print(f"Fresh news collected: {len(news)}")
    print(f"Fresh jobs collected: {len(jobs)}")

    # 5. Apply Entity Resolution
    print("\n[5] Applying Entity Resolution...")
    run_entity_resolution()

    # 6. Export to CSVs
    print("\n[6] Exporting Datasets to CSV...")
    run_csv_export()

    print("\n" + "=" * 60)
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULY")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())