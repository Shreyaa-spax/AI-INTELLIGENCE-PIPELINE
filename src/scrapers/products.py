import asyncio
import aiohttp
import json
import os
import re
from datetime import datetime, timezone

# We use the community-curated AI tools list main file containing 19,000+ products
BASE_URL = "https://raw.githubusercontent.com/lakey009/AI-Tools-List/main/AIToolsList.json"

def clean_name(handle):
    # E.g. "scrip-ai" -> "Scrip AI"
    if not handle:
        return "Unknown"
    # Replace dashes/underscores with space and title case
    cleaned = handle.replace("-", " ").replace("_", " ")
    return cleaned.title()

def infer_startup_name(product_name, website):
    # Fallback/inferred startup name from domain or product name
    if website:
        # Extract domain name without www. and extension
        match = re.search(r"https?://(?:www\.)?([^/.]+)", website)
        if match:
            return match.group(1).title()
    return clean_name(product_name)

def infer_pricing_model(description):
    desc = (description or "").lower()
    if "freemium" in desc or "free trial" in desc or "free tier" in desc or "free version" in desc:
        return "FREEMIUM"
    elif "free" in desc:
        return "FREE"
    elif "enterprise" in desc or "corporate" in desc:
        return "ENTERPRISE"
    elif "paid" in desc or "subscription" in desc or "pricing" in desc or "price" in desc or "dollar" in desc or "$" in desc:
        return "PAID"
    else:
        return "FREEMIUM"  # Consistent fallback handling strategy

def make_product_record(name, website, startup_name, pricing_model):
    return {
        "schemaVersion": "1.0",
        "recordType": "PRODUCT",
        "source": {
            "name": "AI Tools List",
            "url": website if website else "https://github.com/lakey009/AI-Tools-List"
        },
        "content": {
            "productName": name,
            "startupName": startup_name,
            "pricingModel": pricing_model
        },
        "collectedAt": datetime.now(timezone.utc).isoformat()
    }

async def scrape_products():
    print("Starting product scraper (AI Tools List)...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    connector = aiohttp.TCPConnector(limit=5)
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        try:
            async with session.get(BASE_URL, timeout=30) as response:
                print(f"Status: {response.status}")
                if response.status != 200:
                    print("Failed to download products dataset")
                    return []
                text_data = await response.text()
                products_data = json.loads(text_data)
        except Exception as error:
            print("Request failed:", error)
            return []

    records = []
    seen = set()

    for item in products_data:
        handle = item.get("handle")
        website = item.get("website")
        description = item.get("description")

        # Fallback to handle if handle is missing but website is present
        if not handle and website:
            handle = website.split("//")[-1].split(".")[0]

        if not handle:
            continue

        # Standardize product url/name for deduping
        url_key = (website or "").strip().lower()
        if url_key and url_key in seen:
            continue
        if url_key:
            seen.add(url_key)

        p_name = clean_name(handle)
        startup_name = infer_startup_name(handle, website)
        pricing = infer_pricing_model(description)

        record = make_product_record(
            name=p_name,
            website=website,
            startup_name=startup_name,
            pricing_model=pricing
        )
        records.append(record)
        
        if len(records) >= 1100:
            break

    print(f"Ingested {len(records)} unique products.")
    return records

async def main():
    records = await scrape_products()
    os.makedirs("data", exist_ok=True)
    with open("data/products.json", "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)
    print(f"Saved {len(records)} products to data/products.json.")

if __name__ == "__main__":
    asyncio.run(main())